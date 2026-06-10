"""Match Day #2 — motore evento LIVE (Fase 1).

Un EVENT è generico (`kind` friendly|tournament_match) così il torneo lo riusa:
una partita di torneo è un event il cui `slate` = i giocatori di 2 nazioni.

Prezzi CONDIVISI: i tick-evento muovono i prezzi REALI degli atleti dello slate via
lo STESSO motore SORPRESA dei round (`feed → surprise → apply_tick → market_price`),
così il trading live riusa `execute_buy/sell` invariati. Mentre un evento è LIVE lo
slate è marcato `in_event` ed è ESCLUSO dal round globale (no doppio movimento).

Guardie idempotenti (come i round): claim atomico del tick (no doppio avanzamento su
fire ravvicinati / redeploy), un solo evento LIVE alla volta, close idempotente.
NESSUNA leva, NESSUN premio in questa fase.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from app.market.hybrid_pricing import anchor_price, effective_deviation, market_price
from app.market.rounds import describe_round
from app.models.common import utc_now
from app.pricing.engine import apply_tick
from app.pricing.feed import PerformanceFeedProvider
from app.pricing.performance import raw_performance_pct, surprise_pct

# Range di indici DEDICATO ai tick-evento: disgiunto dai round live (1,2,3…),
# dal seed e dal campionamento atteso (900_000) → determinismo senza collisioni.
MATCH_DAY_IDX_BASE = 500_000


def _naive(dt: datetime) -> datetime:
    """UTC naive (Mongo restituisce datetime senza tzinfo) — coerente col resto del codice."""
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


async def _claim_seq(db) -> int:
    """Numero di sequenza progressivo dell'evento (namespacing deterministico dei tick)."""
    d = await db.match_day_state.find_one_and_update(
        {"_id": "matchday"}, {"$inc": {"next_seq": 1}},
        upsert=True, return_document=ReturnDocument.AFTER,
    )
    return int(d["next_seq"])


async def open_event(db, *, slate, kind: str = "friendly", window_min: int = 20,
                     now: datetime | None = None, tournament_id=None,
                     match_meta: dict | None = None) -> dict:
    """Apre un evento LIVE. Idempotente: se ne esiste già uno LIVE lo ritorna (no doppio).

    Marca lo slate `in_event=True` → escluso dal round globale finché l'evento è LIVE.
    """
    now = now or utc_now()
    existing = await db.events.find_one({"status": "live"})
    if existing:
        return existing
    seq = await _claim_seq(db)
    doc = {
        "_id": ObjectId(), "kind": kind, "tournament_id": tournament_id,
        "match_meta": match_meta, "status": "live", "slate": list(slate), "seq": seq,
        "opens_at": now, "closes_at": now + timedelta(minutes=window_min),
        "current_tick": 0, "last_tick_at": None,
        "created_at": now, "updated_at": now,
    }
    await db.events.insert_one(doc)
    await db.athletes.update_many(
        {"_id": {"$in": list(slate)}},
        {"$set": {"in_event": True, "event_id": doc["_id"]}},
    )
    return doc


async def run_event_tick(db, *, event_id, feed: PerformanceFeedProvider, gain: float = 1.0,
                         min_gap_seconds: float = 0.0, now: datetime | None = None) -> dict:
    """Un tick-evento: muove SOLO lo slate via il motore sorpresa. Idempotente.

    `min_gap_seconds>0` (scheduler) = guardia anti-doppio: un secondo fire ravvicinato è
    no-op (`skipped`). Il claim del tick è ATOMICO (come `_claim_round`).
    """
    now = now or utc_now()
    filt: dict = {"_id": event_id, "status": "live"}
    if min_gap_seconds and min_gap_seconds > 0:
        cutoff = now - timedelta(seconds=min_gap_seconds)
        filt = {"_id": event_id, "status": "live",
                "$or": [{"last_tick_at": None}, {"last_tick_at": {"$lte": cutoff}}]}
    doc = await db.events.find_one_and_update(
        filt, {"$inc": {"current_tick": 1}, "$set": {"last_tick_at": now, "updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        return {"skipped": True, "reason": "guard_or_not_live", "event_id": event_id}

    tick = int(doc["current_tick"])
    seq = int(doc["seq"])
    round_idx = MATCH_DAY_IDX_BASE + seq * 1000 + tick
    athletes = await db.athletes.find(
        {"_id": {"$in": doc["slate"]}, "status": "ACTIVE"}
    ).to_list(length=100_000)

    movers: list[dict] = []
    for a in athletes:
        role = a["role"]
        rr = feed.round_performance(a, round_idx)
        raw = raw_performance_pct(role, rr.perf)
        expected = float(a.get("expected_perf_pct") or 0.0)
        pct = surprise_pct(role, raw, expected, gain=gain)

        equo = anchor_price(a)
        ini = float(a["prezzo_iniziale_eur"])
        tk = apply_tick(prezzo_corrente=equo, prezzo_iniziale=ini, perf_pct=pct)
        new_equo = tk.new_price
        dev_now = effective_deviation(a, now)
        new_price = market_price(new_equo, dev_now, ini)
        reason = describe_round(role, rr)

        await db.athletes.update_one(
            {"_id": a["_id"]},
            {"$set": {"prezzo_equo_eur": new_equo, "prezzo_corrente_eur": new_price,
                      "updated_at": now}},
        )
        await db.price_history.insert_one({
            "athlete_id": a["_id"], "event_id": event_id, "tick": tick,
            "prezzo": new_price, "perf_pct": pct, "reason": "match_day",
            "floored": tk.floored, "ts": now,
        })
        await db.event_events.insert_one({
            "event_id": event_id, "athlete_id": a["_id"], "tick": tick,
            "stats": rr.stats, "perf_pct": pct, "reason": reason, "ts": now,
        })
        if pct != 0.0:
            movers.append({"athlete_id": str(a["_id"]), "label": a.get("display_label"),
                           "role": role, "perf_pct": pct, "reason": reason})

    movers.sort(key=lambda m: m["perf_pct"], reverse=True)
    return {"event_id": event_id, "tick": tick, "slate": len(athletes),
            "moved": len(movers), "top_up": movers[:5]}


async def close_event(db, *, event_id, now: datetime | None = None) -> dict:
    """Chiude l'evento e sblocca lo slate (`in_event` rimosso). Idempotente.

    Il passaggio live→closed è ATOMICO: un secondo close è no-op (`already_closed`).
    """
    now = now or utc_now()
    res = await db.events.update_one(
        {"_id": event_id, "status": "live"},
        {"$set": {"status": "closed", "closed_at": now, "updated_at": now}},
    )
    if res.modified_count == 0:
        ev = await db.events.find_one({"_id": event_id})
        if ev and ev["status"] == "closed":
            return {"already_closed": True, "event_id": event_id, "status": "closed"}
        return {"not_found": True, "event_id": event_id}
    ev = await db.events.find_one({"_id": event_id})
    await db.athletes.update_many(
        {"_id": {"$in": ev.get("slate", [])}},
        {"$unset": {"in_event": "", "event_id": ""}},
    )
    return {"status": "closed", "event_id": event_id}


async def get_current_match_day(db, now: datetime | None = None) -> dict | None:
    """Stato dell'evento LIVE corrente + prezzi dello slate + countdown. None se nessuno."""
    now = now or utc_now()
    ev = await db.events.find_one({"status": "live"})
    if not ev:
        return None
    athletes = await db.athletes.find(
        {"_id": {"$in": ev["slate"]}}
    ).to_list(length=100_000)
    slate = [{"athlete_id": str(a["_id"]), "label": a.get("display_label"),
              "role": a.get("role"), "prezzo": a.get("prezzo_corrente_eur")}
             for a in athletes]
    seconds_left = max(0, int((_naive(ev["closes_at"]) - _naive(now)).total_seconds()))
    return {
        "event_id": ev["_id"], "status": ev["status"], "kind": ev["kind"],
        "tournament_id": ev.get("tournament_id"), "tick": ev.get("current_tick", 0),
        "opens_at": ev["opens_at"], "closes_at": ev["closes_at"],
        "seconds_left": seconds_left, "slate": slate,
    }
