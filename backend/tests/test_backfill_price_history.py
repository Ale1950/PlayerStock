"""Backfill storico prezzi € (sparkline/var%): in banda, fine=corrente, idempotente."""
from __future__ import annotations

import pytest
from bson import ObjectId

from app.config.pricing_constants import DEVIAZIONE_CAP, FLOOR_PCT_PREZZO_INIZIALE


def _athlete(cur, ini=None):
    ini = ini if ini is not None else cur
    return {
        "_id": ObjectId(), "sport_id": "calcio", "status": "ACTIVE", "role": "ATT",
        "prezzo_corrente_eur": cur, "prezzo_iniziale_eur": ini, "prezzo_equo_eur": cur,
        "float_quote": 1_000_000,
    }


@pytest.mark.asyncio
async def test_history_in_band_ends_at_current_and_only_touches_history(mock_db):
    from tools.backfill_price_history import backfill_price_history

    athletes = [_athlete(0.50), _athlete(6.58), _athlete(83.00)]
    await mock_db.athletes.insert_many(athletes)
    await mock_db.holdings.insert_one({"user_id": ObjectId(), "quantity": 5})
    before = {a["_id"]: a["prezzo_corrente_eur"] for a in athletes}

    rep = await backfill_price_history(mock_db)
    assert rep["athletes"] == 3
    assert rep["per_athlete"] == 90

    for a in athletes:
        pts = await mock_db.price_history.find({"athlete_id": a["_id"]}).to_list(length=1000)
        assert len(pts) == 90
        assert all(p["reason"] == "backfill" for p in pts)
        cur = before[a["_id"]]
        ini = a["prezzo_iniziale_eur"]
        floor, tetto = FLOOR_PCT_PREZZO_INIZIALE * ini, cur * (1.0 + DEVIAZIONE_CAP)
        for p in pts:
            assert floor - 1e-9 <= p["prezzo"] <= tetto + 1e-9
        # punto più recente = prezzo corrente ESATTO (var% e value=prezzo×1M coerenti)
        latest = max(pts, key=lambda p: p["ts"])
        assert latest["prezzo"] == pytest.approx(cur)

    # prezzo corrente atleti INVARIATO; holdings non toccate
    after = {a["_id"]: (await mock_db.athletes.find_one({"_id": a["_id"]}))["prezzo_corrente_eur"]
             for a in athletes}
    assert after == before
    assert await mock_db.holdings.count_documents({}) == 1


@pytest.mark.asyncio
async def test_idempotent_and_deterministic(mock_db):
    from tools.backfill_price_history import backfill_price_history

    a = _athlete(10.0)
    await mock_db.athletes.insert_one(a)
    await backfill_price_history(mock_db)
    first = sorted([p["prezzo"] for p in
                    await mock_db.price_history.find({"athlete_id": a["_id"]}).to_list(length=1000)])
    await backfill_price_history(mock_db)
    rows = await mock_db.price_history.find({"athlete_id": a["_id"]}).to_list(length=1000)
    assert len(rows) == 90  # non raddoppia (cancella i propri prima di riscrivere)
    second = sorted([p["prezzo"] for p in rows])
    assert first == second  # deterministico


@pytest.mark.asyncio
async def test_purges_out_of_band_stale_points(mock_db):
    """Punti pre-migrazione fuori banda (scala Cr) vengono eliminati; in-banda restano."""
    from tools.backfill_price_history import backfill_price_history

    a = _athlete(83.0)
    await mock_db.athletes.insert_one(a)
    await mock_db.price_history.insert_many([
        {"athlete_id": a["_id"], "prezzo": 0.0183, "reason": "snapshot"},   # stale Cr → out
        {"athlete_id": a["_id"], "prezzo": 83.0, "reason": "trade"},        # valido € → resta
    ])
    await backfill_price_history(mock_db)
    prezzi = [p["prezzo"] for p in
              await mock_db.price_history.find({"athlete_id": a["_id"]}).to_list(length=1000)]
    assert 0.0183 not in prezzi                     # stale rimosso
    assert 83.0 in prezzi                           # punto valido conservato
    assert min(prezzi) >= FLOOR_PCT_PREZZO_INIZIALE * 83.0 - 1e-9


@pytest.mark.asyncio
async def test_volatility_varies_between_athletes(mock_db):
    """Differenziazione realistica: non tutti gli atleti hanno la stessa ampiezza."""
    from tools.backfill_price_history import backfill_price_history

    athletes = [_athlete(20.0) for _ in range(12)]
    await mock_db.athletes.insert_many(athletes)
    await backfill_price_history(mock_db)
    spans = []
    for a in athletes:
        ps = [p["prezzo"] for p in
              await mock_db.price_history.find({"athlete_id": a["_id"]}).to_list(length=1000)]
        spans.append(max(ps) - min(ps))
    # alcuni mossi, altri tranquilli → varianza tra le ampiezze
    assert max(spans) > 2 * (min(spans) + 1e-6)
