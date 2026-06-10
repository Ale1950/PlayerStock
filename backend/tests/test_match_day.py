"""Match Day #2 — Fase 1: event generico + slate + tick-evento + stato.

- event generico (kind friendly|tournament_match), riusabile dal torneo;
- open idempotente (1 solo LIVE alla volta), slate marcato in_event;
- tick-evento muove SOLO lo slate, via il motore sorpresa (prezzi condivisi);
- guardia idempotente sul tick (no doppio avanzamento su fire ravvicinati);
- round globale ESCLUDE lo slate mentre l'evento è LIVE;
- close idempotente, sblocca lo slate.
NESSUNA leva, NESSUN premio in questa fase.
"""
from __future__ import annotations

import pytest
from bson import ObjectId

from app.market.match_day import (
    close_event,
    get_current_match_day,
    open_event,
    run_event_tick,
)
from app.market.rounds import run_round
from app.models.common import utc_now
from app.pricing.feed import SyntheticPerformanceProvider

FEED = SyntheticPerformanceProvider()


def _athlete(role="ATT", score=1.8, **extra):
    base = {
        "_id": ObjectId(), "sport_id": "calcio", "status": "ACTIVE", "role": role,
        "source_external_id": str(ObjectId()), "display_label": "X. Test",
        "score_performance": score, "minutaggio_pct": 0.95,
        "prezzo_iniziale_eur": 10.0, "prezzo_equo_eur": 10.0, "prezzo_corrente_eur": 10.0,
        "deviazione": 0.0,
    }
    base.update(extra)
    return base


async def _seed(db, n_slate=6, n_other=4):
    slate = [_athlete(role=r, score=1.9) for _ in range(n_slate // 4 + 1) for r in ("ATT", "CC", "DIF", "POR")][:n_slate]
    other = [_athlete(role="ATT", score=1.9) for _ in range(n_other)]
    await db.athletes.insert_many(slate + other)
    return [a["_id"] for a in slate], [a["_id"] for a in other]


@pytest.mark.asyncio
async def test_open_event_single_live(mock_db):
    slate, _ = await _seed(mock_db)
    ev = await open_event(mock_db, slate=slate, kind="friendly", window_min=20)
    assert ev["status"] == "live"
    assert ev["kind"] == "friendly"
    assert set(ev["slate"]) == set(slate)
    # slate marcato in_event
    for aid in slate:
        a = await mock_db.athletes.find_one({"_id": aid})
        assert a.get("in_event") is True
    # un secondo open mentre c'è un LIVE → ritorna lo STESSO evento (no doppio live)
    ev2 = await open_event(mock_db, slate=slate, kind="friendly", window_min=20)
    assert ev2["_id"] == ev["_id"]
    assert await mock_db.events.count_documents({"status": "live"}) == 1


@pytest.mark.asyncio
async def test_event_tick_moves_only_slate(mock_db):
    slate, other = await _seed(mock_db)
    ev = await open_event(mock_db, slate=slate, window_min=20)
    rep = await run_event_tick(mock_db, event_id=ev["_id"], feed=FEED, gain=2.5)
    assert rep["tick"] == 1 and rep["event_id"] == ev["_id"]

    # gli atleti NON nello slate restano fermi
    for aid in other:
        a = await mock_db.athletes.find_one({"_id": aid})
        assert a["prezzo_equo_eur"] == 10.0
    # price_history dell'evento taggato
    ph = await mock_db.price_history.find({"reason": "match_day"}).to_list(length=100)
    assert len(ph) == len(slate)
    assert all(p["event_id"] == ev["_id"] for p in ph)


@pytest.mark.asyncio
async def test_event_tick_idempotent_guard(mock_db):
    slate, _ = await _seed(mock_db)
    ev = await open_event(mock_db, slate=slate, window_min=20)
    now = utc_now()
    r1 = await run_event_tick(mock_db, event_id=ev["_id"], feed=FEED, gain=1.0, now=now, min_gap_seconds=10)
    r2 = await run_event_tick(mock_db, event_id=ev["_id"], feed=FEED, gain=1.0, now=now, min_gap_seconds=10)
    assert r1["tick"] == 1
    assert r2.get("skipped") is True
    doc = await mock_db.events.find_one({"_id": ev["_id"]})
    assert doc["current_tick"] == 1


@pytest.mark.asyncio
async def test_global_round_excludes_live_slate(mock_db):
    slate, other = await _seed(mock_db)
    await open_event(mock_db, slate=slate, window_min=20)
    rep = await run_round(mock_db, feed=FEED, gain=2.5)
    # il round globale ha toccato SOLO i non-slate
    assert rep["athletes"] == len(other)
    for aid in slate:
        a = await mock_db.athletes.find_one({"_id": aid})
        assert a["prezzo_equo_eur"] == 10.0  # non mosso dal round globale


@pytest.mark.asyncio
async def test_close_event_clears_in_event_idempotent(mock_db):
    slate, _ = await _seed(mock_db)
    ev = await open_event(mock_db, slate=slate, window_min=20)
    res = await close_event(mock_db, event_id=ev["_id"])
    assert res["status"] == "closed"
    for aid in slate:
        a = await mock_db.athletes.find_one({"_id": aid})
        assert not a.get("in_event")
    # close di nuovo = no-op idempotente
    res2 = await close_event(mock_db, event_id=ev["_id"])
    assert res2.get("already_closed") is True
    assert await mock_db.events.count_documents({"status": "live"}) == 0


@pytest.mark.asyncio
async def test_get_current_match_day(mock_db):
    assert await get_current_match_day(mock_db) is None
    slate, _ = await _seed(mock_db)
    ev = await open_event(mock_db, slate=slate, window_min=20)
    cur = await get_current_match_day(mock_db)
    assert cur is not None
    assert cur["event_id"] == ev["_id"]
    assert cur["status"] == "live"
    assert len(cur["slate"]) == len(slate)
    assert "seconds_left" in cur
