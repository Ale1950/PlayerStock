"""CLI: simula N giornate sintetiche → apply_tick → storico prezzi (Fase 2b).

Dà MOVIMENTO alla borsa nell'MVP (sparkline non vuote, utile anche per testare la
Fase 3 senza utenti reali). Eventi SINTETICI deterministici per (atleta, giornata),
scalati da ruolo + score_performance. NESSUNA pretesa di realismo (DECISIONS.md 2b).

Uso (dalla cartella backend/):
    python -m app.cli.simulate_rounds --rounds 10
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import sys
from datetime import datetime, timedelta

from app.config.pricing_constants import CAP_UTENTE_AZIONI
from app.core.db import close_db, get_db, init_db
from app.core.errors import APIError
from app.market.hybrid_pricing import anchor_price, effective_deviation, market_price
from app.market.trade import execute_buy, execute_sell
from app.models.common import utc_now
from app.pricing.engine import apply_tick
from app.pricing.feed import SyntheticPerformanceProvider
from app.pricing.performance import MatchPerformance, performance_pct

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("simulate_cli")

def _unit(key: str) -> float:
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big") / 2**64


# FONTE UNICA: il generatore vive nel feed a innesto (D10). Qui solo un wrapper di
# compatibilità per la CLI/simulazione (ritorna il `MatchPerformance` per il pricing).
_FEED = SyntheticPerformanceProvider()


def synthetic_round_performance(athlete: dict, round_idx: int) -> MatchPerformance:
    """Giornata sintetica deterministica per l'atleta (delega al feed unificato)."""
    return _FEED.round_performance(athlete, round_idx).perf


async def simulate_rounds(db, n_rounds: int, *, sport_id: str = "calcio") -> dict:
    """Applica n_rounds di tick sintetici a tutti gli atleti; scrive price_history."""
    athletes = await db.athletes.find(
        {"sport_id": sport_id, "status": "ACTIVE"}
    ).to_list(length=10_000)

    moves = 0
    for rnd in range(1, n_rounds + 1):
        for a in athletes:
            perf = synthetic_round_performance(a, rnd)
            pct = performance_pct(a["role"], perf)
            res = apply_tick(
                prezzo_corrente=a["prezzo_corrente_eur"],
                prezzo_iniziale=a["prezzo_iniziale_eur"],
                perf_pct=pct,
            )
            a["prezzo_corrente_eur"] = res.new_price
            await db.athletes.update_one(
                {"_id": a["_id"]},
                {"$set": {"prezzo_corrente_eur": res.new_price, "updated_at": utc_now()}},
            )
            await db.price_history.insert_one({
                "athlete_id": a["_id"],
                "round": rnd,
                "prezzo": res.new_price,
                "perf_pct": pct,
                "floored": res.floored,
                "ts": utc_now(),
            })
            if pct != 0.0:
                moves += 1

    return {
        "rounds": n_rounds,
        "athletes": len(athletes),
        "history_points": n_rounds * len(athletes),
        "moves": moves,
    }


async def apply_rendimento_round(db, *, athlete_id, perf_pct: float, now: datetime) -> dict:
    """Round di rendimento (Fase 2) sull'ÀNCORA (prezzo_equo), poi ricalcola il
    prezzo di mercato componendo la deviazione di trading corrente (Fase 3b)."""
    a = await db.athletes.find_one({"_id": athlete_id})
    if not a:
        return {}
    equo = anchor_price(a)
    prezzo_iniziale = a["prezzo_iniziale_eur"]
    tick = apply_tick(prezzo_corrente=equo, prezzo_iniziale=prezzo_iniziale, perf_pct=perf_pct)
    new_equo = tick.new_price
    dev_now = effective_deviation(a, now)
    new_price = market_price(new_equo, dev_now, prezzo_iniziale)
    await db.athletes.update_one(
        {"_id": athlete_id},
        {"$set": {"prezzo_equo_eur": new_equo, "prezzo_corrente_eur": new_price,
                  "updated_at": now}},
    )
    await db.price_history.insert_one({
        "athlete_id": athlete_id, "prezzo": new_price, "perf_pct": perf_pct,
        "reason": "rendimento", "floored": tick.floored, "ts": now,
    })
    return {"prezzo_equo": new_equo, "prezzo": new_price}


async def _trading_step(db, athletes: list[dict], trader_ids: list, day: int, now: datetime) -> int:
    """Pressione di trading simulata: ogni trader prova un ordine deterministico
    entro cap 3% + holding 7gg (i rifiuti del banco sono attesi e ignorati)."""
    trades = 0
    n = len(athletes)
    for ti, uid in enumerate(trader_ids):
        a = athletes[int(_unit(f"pick:{ti}:{day}") * n) % n]
        aid = a["_id"]
        qty = 1 + int(_unit(f"qty:{ti}:{day}") * (CAP_UTENTE_AZIONI // 3))  # < cap
        buy = _unit(f"side:{ti}:{day}") < 0.6  # bias all'acquisto
        try:
            if buy:
                await execute_buy(db, user_id=uid, athlete_id=aid, qty=qty, now=now)
            else:
                await execute_sell(db, user_id=uid, athlete_id=aid, qty=qty, now=now)
            trades += 1
        except (APIError, ValueError):
            pass  # fondi/cap/holding insufficienti → ordine saltato
    return trades


async def _engagement_step(db, trader_ids: list, day: int, now, faucet_config: dict) -> float:
    """Faucet crediti da engagement: ogni trader guadagna EP realistici (~2–8/gg) e
    riceve il bonus-crediti a scaglioni (idempotente per evento)."""
    from app.economy.credit_faucet import grant_engagement_credits
    injected = 0.0
    for ti, uid in enumerate(trader_ids):
        ep = 2.0 + _unit(f"ep:{ti}:{day}") * 6.0  # 2..8 EP/giorno
        res = await grant_engagement_credits(
            db, user_id=uid, event_id=f"eng:{ti}:{day}", ep=ep, now=now, config=faucet_config,
        )
        injected += res["credits"]
    return injected


async def simulate_economy(
    db, *, days: int, trader_ids: list, sport_id: str = "calcio", faucet_config: dict | None = None,
) -> dict:
    """Simula `days` giornate: rendimento sull'àncora + pressione di trading
    (+ faucet crediti da engagement se `faucet_config`). Metriche per il report."""
    now0 = utc_now()
    total_trades = 0
    credits_injected = 0.0
    for day in range(1, days + 1):
        now = now0 + timedelta(days=day)
        athletes = await db.athletes.find({"sport_id": sport_id, "status": "ACTIVE"}).to_list(length=10_000)
        for a in athletes:
            perf = synthetic_round_performance(a, day)
            pct = performance_pct(a["role"], perf)
            await apply_rendimento_round(db, athlete_id=a["_id"], perf_pct=pct, now=now)
        athletes = await db.athletes.find({"sport_id": sport_id, "status": "ACTIVE"}).to_list(length=10_000)
        total_trades += await _trading_step(db, athletes, trader_ids, day, now)
        if faucet_config is not None:
            credits_injected += await _engagement_step(db, trader_ids, day, now, faucet_config)

    # ─── metriche ───
    athletes = await db.athletes.find({"sport_id": sport_id, "status": "ACTIVE"}).to_list(length=10_000)
    ratios = [a["prezzo_corrente_eur"] / a["prezzo_iniziale_eur"] for a in athletes if a["prezzo_iniziale_eur"]]
    devs = [abs(a.get("deviazione", 0.0)) for a in athletes]
    prices = [a["prezzo_corrente_eur"] for a in athletes]
    house = await db.house_account.find_one({"_id": "house"})
    fee_revenue = float(house.get("fees_collected", 0.0)) if house else 0.0
    avg_price = (sum(prices) / len(prices)) if prices else 0.0
    cap_cost = CAP_UTENTE_AZIONI * avg_price * 1.035
    floored = sum(1 for a in athletes if a["prezzo_corrente_eur"] <= 0.1001 * a["prezzo_iniziale_eur"])
    return {
        "days": days,
        "athletes": len(athletes),
        "traders": len(trader_ids),
        "trades_executed": total_trades,
        "fee_revenue": fee_revenue,
        "credits_injected": credits_injected,
        "net_credit_flow": credits_injected - fee_revenue,
        "price_ratio_min": min(ratios) if ratios else 0.0,
        "price_ratio_max": max(ratios) if ratios else 0.0,
        "deviation_abs_max": max(devs) if devs else 0.0,
        "deviation_abs_avg": (sum(devs) / len(devs)) if devs else 0.0,
        "avg_price": avg_price,
        "cap_buy_cost_at_avg": cap_cost,
        "cap_buys_affordable_10k": (10_000.0 / cap_cost) if cap_cost else 0.0,
        "floored_count": floored,
    }


async def main(n_rounds: int) -> int:
    init_db()
    db = get_db()
    stats = await simulate_rounds(db, n_rounds)
    logger.info(
        "DONE | rounds=%d | athletes=%d | history_points=%d | moves=%d",
        stats["rounds"], stats["athletes"], stats["history_points"], stats["moves"],
    )
    close_db()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=10)
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.rounds)))
