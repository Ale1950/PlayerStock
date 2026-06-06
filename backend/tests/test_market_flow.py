"""RED→GREEN: net order flow finestra → mercato% → apply_tick → price_history."""
from __future__ import annotations

from datetime import timedelta

import pytest
from bson import ObjectId

from app.market.market_pct import apply_market_flow
from app.models.common import utc_now


async def _athlete(db, price=0.02):
    aid = ObjectId()
    await db.athletes.insert_one({
        "_id": aid, "sport_id": "calcio", "status": "ACTIVE", "role": "ATT",
        "prezzo_corrente_eur": price, "prezzo_iniziale_eur": price,
    })
    return aid


async def test_net_buy_pressure_moves_price_up(mock_db):
    aid = await _athlete(mock_db, price=0.02)
    now = utc_now()
    # net = 10 buy - 3 sell = 7 -> bucket 6-20 -> +0.020
    await mock_db.orders.insert_one({"athlete_id": aid, "side": "buy", "qty": 10, "created_at": now})
    await mock_db.orders.insert_one({"athlete_id": aid, "side": "sell", "qty": 3, "created_at": now})

    stats = await apply_market_flow(mock_db, since=now - timedelta(hours=1))

    a = await mock_db.athletes.find_one({"_id": aid})
    assert a["prezzo_corrente_eur"] == pytest.approx(0.02 * 1.020)
    assert stats["athletes_moved"] == 1
    assert await mock_db.price_history.count_documents({"reason": "market"}) == 1


async def test_no_flow_no_move(mock_db):
    aid = await _athlete(mock_db, price=0.02)
    stats = await apply_market_flow(mock_db, since=utc_now() - timedelta(hours=1))
    a = await mock_db.athletes.find_one({"_id": aid})
    assert a["prezzo_corrente_eur"] == pytest.approx(0.02)
    assert stats["athletes_moved"] == 0


async def test_flow_respects_floor(mock_db):
    aid = await _athlete(mock_db, price=0.02)
    # forza prezzo vicino al floor e pressione di vendita
    await mock_db.athletes.update_one({"_id": aid}, {"$set": {"prezzo_corrente_eur": 0.00205}})
    now = utc_now()
    await mock_db.orders.insert_one({"athlete_id": aid, "side": "sell", "qty": 50, "created_at": now})
    await apply_market_flow(mock_db, since=now - timedelta(hours=1))
    a = await mock_db.athletes.find_one({"_id": aid})
    assert a["prezzo_corrente_eur"] >= 0.10 * 0.02 - 1e-12  # floor 10% iniziale
