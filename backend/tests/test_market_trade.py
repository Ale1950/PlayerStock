"""RED→GREEN: esecuzione buy/sell contro la CASA (pool a due lati)."""
from __future__ import annotations

from datetime import timedelta

import pytest
from bson import ObjectId

from app.core.errors import APIError
from app.market.trade import execute_buy, execute_sell
from app.models.common import utc_now


async def _setup(db, *, balance=100.0, price=0.02, pool=1_000_000):
    uid, aid = ObjectId(), ObjectId()
    await db.user_wallets.insert_one(
        {"user_id": uid, "balance_credits": balance, "updated_at": utc_now()}
    )
    await db.athletes.insert_one({
        "_id": aid, "sport_id": "calcio", "status": "ACTIVE", "role": "ATT",
        "prezzo_corrente_crediti": price, "prezzo_iniziale_crediti": price,
        "float_quote": 1_000_000, "primary_pool_qty": pool,
        "circulating_qty": 1_000_000 - pool,
    })
    return uid, aid


async def test_buy_updates_wallet_pool_holding(mock_db):
    uid, aid = await _setup(mock_db)
    await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=100)

    wallet = await mock_db.user_wallets.find_one({"user_id": uid})
    assert wallet["balance_credits"] == pytest.approx(100.0 - 2.0 * 1.035)  # 97.93

    a = await mock_db.athletes.find_one({"_id": aid})
    assert a["primary_pool_qty"] == 999_900
    assert a["circulating_qty"] == 100

    h = await mock_db.holdings.find_one({"user_id": uid, "athlete_id": aid})
    assert h["quantity"] == 100
    assert len(h["lots"]) == 1
    assert await mock_db.trades.count_documents({}) == 1
    assert await mock_db.orders.count_documents({"side": "buy"}) == 1


async def test_buy_insufficient_funds(mock_db):
    uid, aid = await _setup(mock_db, balance=1.0)
    with pytest.raises(APIError):
        await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=100)


async def test_buy_pool_sold_out(mock_db):
    uid, aid = await _setup(mock_db, pool=50)
    with pytest.raises(APIError):
        await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=100)


async def test_buy_cap_exceeded(mock_db):
    uid, aid = await _setup(mock_db, balance=10_000_000.0)
    with pytest.raises(APIError):
        await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=30_001)


async def test_sell_blocked_before_7_days(mock_db):
    uid, aid = await _setup(mock_db)
    await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=100)
    with pytest.raises(APIError):
        await execute_sell(mock_db, user_id=uid, athlete_id=aid, qty=50)  # appena comprate


async def test_sell_after_holding_updates_state(mock_db):
    uid, aid = await _setup(mock_db)
    t0 = utc_now()
    await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=100, now=t0)

    later = t0 + timedelta(days=8)
    await execute_sell(mock_db, user_id=uid, athlete_id=aid, qty=40, now=later)

    h = await mock_db.holdings.find_one({"user_id": uid, "athlete_id": aid})
    assert h["quantity"] == 60
    a = await mock_db.athletes.find_one({"_id": aid})
    assert a["primary_pool_qty"] == 999_940
    assert a["circulating_qty"] == 60


async def test_fees_accrue_to_house(mock_db):
    uid, aid = await _setup(mock_db)
    t0 = utc_now()
    await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=100, now=t0)
    await execute_sell(mock_db, user_id=uid, athlete_id=aid, qty=100, now=t0 + timedelta(days=8))

    house = await mock_db.house_account.find_one({"_id": "house"})
    # fee_buyer (2.0*0.035) + fee_seller (2.0*0.035) = 0.14
    assert house["fees_collected"] == pytest.approx(0.14)
