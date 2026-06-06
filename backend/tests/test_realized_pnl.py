"""TDD: P&L realizzato — costo FIFO delle quote vendute, registrato sull'ordine."""
from __future__ import annotations

from datetime import timedelta

import pytest
from bson import ObjectId

from app.market.rules import consume_lots_fifo_with_cost
from app.market.trade import execute_buy, execute_sell
from app.models.common import utc_now


def test_consume_lots_with_cost_fifo():
    t = utc_now()
    lots = [
        {"qty": 100, "price": 0.01, "acquired_at": t},
        {"qty": 50, "price": 0.02, "acquired_at": t + timedelta(seconds=1)},
    ]
    remaining, cost = consume_lots_fifo_with_cost(lots, 120)
    # 100×0.01 + 20×0.02 = 1.0 + 0.4 = 1.4 ; restano 30×0.02
    assert cost == pytest.approx(1.4)
    assert len(remaining) == 1
    assert remaining[0]["qty"] == 30
    assert remaining[0]["price"] == pytest.approx(0.02)


def test_consume_all_lots_cost():
    t = utc_now()
    lots = [{"qty": 100, "price": 0.05, "acquired_at": t}]
    remaining, cost = consume_lots_fifo_with_cost(lots, 100)
    assert cost == pytest.approx(5.0)
    assert remaining == []


async def _setup(db, *, balance=10_000.0, price=0.02):
    uid, aid = ObjectId(), ObjectId()
    await db.user_wallets.insert_one({"user_id": uid, "balance_eur": balance, "updated_at": utc_now()})
    await db.athletes.insert_one({
        "_id": aid, "sport_id": "calcio", "status": "ACTIVE", "role": "ATT",
        "prezzo_corrente_eur": price, "prezzo_iniziale_eur": price,
        "float_quote": 1_000_000, "primary_pool_qty": 1_000_000, "circulating_qty": 0,
    })
    return uid, aid


async def test_sell_records_realized_pnl_on_order(mock_db):
    uid, aid = await _setup(mock_db, price=0.02)
    t0 = utc_now()
    await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=1_000, now=t0)  # costo 1000×0.02=20
    later = t0 + timedelta(days=8)
    res = await execute_sell(mock_db, user_id=uid, athlete_id=aid, qty=1_000, now=later)

    order = await mock_db.orders.find_one({"side": "sell"})
    # ricavo lordo - costo base venduto (le fee sono separate)
    assert order["cost_basis_sold"] == pytest.approx(20.0)
    assert order["realized_pnl"] == pytest.approx(res["gross"] - 20.0)
