"""Round di performance → muove il PREZZO EQUO (ancora). Motore di vivacità (D10).

Per ogni round: il feed prestazioni genera gli eventi del giocatore → `performance_pct`
(coeff. Gioco 5 × gain, clamp RANGE_CLAMP) → sposta `prezzo_equo_eur` via `apply_tick`
(floor 10%), poi il prezzo di mercato ricompone la DEVIAZIONE di trading decaduta.
Performance = fondamentale (ancora) · trading = sentiment (deviazione): SEPARATI.

UNICA FONTE: gli stessi eventi si sommano in `season_stats` (mostrate) e finiscono in
`round_events` (citabili dal feed News). Stato globale in `market_state{current_round}`.
NON inietta valuta → nessun impatto su inflazione/faucet/economia €.
"""
from __future__ import annotations

from datetime import datetime

from app.market.hybrid_pricing import anchor_price, effective_deviation, market_price
from app.models.common import utc_now
from app.pricing.engine import apply_tick
from app.pricing.feed import PerformanceFeedProvider, RoundResult
from app.pricing.performance import raw_performance_pct, surprise_pct

_SEASON_FIELDS = ("presenze", "minuti", "gol", "assist", "ammonizioni", "parate")


def describe_round(role: str, rr: RoundResult) -> str:
    """Frase sintetica sull'evento chiave del round (per News + spiegazioni)."""
    s, p = rr.stats, rr.perf
    if s["presenze"] == 0:
        return "in panchina"
    if p.espulso:
        return "espulso"
    if s["gol"] >= 2:
        return "doppietta"
    if s["gol"] == 1 and s["assist"] >= 1:
        return "gol e assist"
    if s["gol"] == 1:
        return "1 gol"
    if role == "POR" and (s.get("parate") or 0) >= 3:
        return f"{s['parate']} parate"
    if s["assist"] >= 1:
        return f"{s['assist']} assist"
    # "gol subiti" / "porta inviolata" = effetto-squadra, MA come motivo headline ha senso
    # solo per chi difende (POR/DIF). Per ATT/CC non si titola sui gol subiti (vedi D10).
    if role in ("POR", "DIF"):
        if p.gol_subiti == 0:
            return "porta inviolata"
        if p.gol_subiti >= 2:
            return f"{p.gol_subiti} gol subiti"
    if s["ammonizioni"] >= 2:
        return "doppio giallo"
    return "prestazione regolare"


async def _get_round(db) -> int:
    st = await db.market_state.find_one({"_id": "market"})
    return int(st.get("current_round", 0)) if st else 0


async def run_round(db, *, feed: PerformanceFeedProvider, gain: float = 1.0,
                    now: datetime | None = None, sport_id: str = "calcio") -> dict:
    """Esegue UN round su tutti gli atleti attivi. Ritorna riepilogo + top movers."""
    now = now or utc_now()
    rnd = await _get_round(db) + 1
    athletes = await db.athletes.find({"sport_id": sport_id, "status": "ACTIVE"}).to_list(length=100_000)

    movers: list[dict] = []
    for a in athletes:
        role = a["role"]
        rr = feed.round_performance(a, rnd)
        # prezzo su SORPRESA = (punteggio reale − atteso) × gain, clamp. Atteso FISSO dal
        # seed; fallback 0 solo difensivo (in pratica sempre presente dopo il seed).
        raw = raw_performance_pct(role, rr.perf)
        expected = float(a.get("expected_perf_pct") or 0.0)
        pct = surprise_pct(role, raw, expected, gain=gain)

        equo = anchor_price(a)
        ini = float(a["prezzo_iniziale_eur"])
        tick = apply_tick(prezzo_corrente=equo, prezzo_iniziale=ini, perf_pct=pct)
        new_equo = tick.new_price
        dev_now = effective_deviation(a, now)
        new_price = market_price(new_equo, dev_now, ini)
        reason = describe_round(role, rr)

        await db.athletes.update_one(
            {"_id": a["_id"]},
            {
                "$set": {"prezzo_equo_eur": new_equo, "prezzo_corrente_eur": new_price,
                         "last_round_stats": rr.stats, "last_round_perf_pct": pct,
                         "last_round_reason": reason, "updated_at": now},
                "$inc": {f"season_stats.{f}": (rr.stats.get(f) or 0) for f in _SEASON_FIELDS},
            },
        )
        await db.round_events.insert_one({
            "athlete_id": a["_id"], "round": rnd, "stats": rr.stats,
            "perf_pct": pct, "reason": reason, "ts": now,
        })
        await db.price_history.insert_one({
            "athlete_id": a["_id"], "round": rnd, "prezzo": new_price, "perf_pct": pct,
            "reason": "round", "floored": tick.floored, "ts": now,
        })
        if pct != 0.0:
            movers.append({"athlete_id": str(a["_id"]), "label": a.get("display_label"),
                           "role": role, "perf_pct": pct, "reason": reason})

    await db.market_state.update_one(
        {"_id": "market"},
        {"$set": {"current_round": rnd, "last_round_at": now}},
        upsert=True,
    )
    movers.sort(key=lambda m: m["perf_pct"], reverse=True)
    return {
        "round": rnd, "athletes": len(athletes), "moved": len(movers),
        "top_up": movers[:5], "top_down": list(reversed(movers[-5:])) if movers else [],
    }


async def seed_previous_season(db, *, feed: PerformanceFeedProvider, rounds: int = 10,
                               gain: float = 1.0, now: datetime | None = None) -> dict:
    """Semina le ultime `rounds` giornate della stagione PRECEDENTE (fittizia): stat e
    prezzi partono 'con una storia', non piatti. = `rounds` × run_round consecutivi."""
    now = now or utc_now()
    last = {}
    for _ in range(rounds):
        last = await run_round(db, feed=feed, gain=gain, now=now)
    return {"seeded_rounds": rounds, "final_round": last.get("round")}
