"""RED→GREEN: regole mercato pure (cap 3%, holding 7gg FIFO, fee 3.5%)."""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.errors import APIError
from app.market.rules import (
    assert_within_cap,
    buy_cost,
    consume_lots_fifo,
    fee_buyer,
    fee_seller,
    sell_proceeds,
    sellable_quantity,
)
from app.models.common import utc_now


def test_cap_ok():
    assert_within_cap(current_qty=20_000, add_qty=10_000)  # = 30.000, ok


def test_cap_exceeded():
    with pytest.raises(APIError):
        assert_within_cap(current_qty=29_999, add_qty=2)


def test_sellable_quantity_respects_7_days():
    now = utc_now()
    lots = [
        {"qty": 100, "acquired_at": now - timedelta(days=8)},   # eleggibile
        {"qty": 50, "acquired_at": now - timedelta(days=7, hours=1)},  # eleggibile
        {"qty": 30, "acquired_at": now - timedelta(days=3)},    # bloccato
    ]
    assert sellable_quantity(lots, now) == 150


def test_consume_lots_fifo():
    now = utc_now()
    lots = [
        {"qty": 100, "acquired_at": now - timedelta(days=10)},
        {"qty": 50, "acquired_at": now - timedelta(days=9)},
    ]
    remaining = consume_lots_fifo(lots, 120)
    assert sum(l["qty"] for l in remaining) == 30
    assert remaining[0]["qty"] == 30  # consumato il lotto più vecchio per intero


def test_consume_lots_fifo_too_much_raises():
    now = utc_now()
    lots = [{"qty": 10, "acquired_at": now}]
    with pytest.raises(ValueError):
        consume_lots_fifo(lots, 11)


def test_fee_and_cost_helpers():
    # qty 100 @ 0.02 = gross 2.0
    assert buy_cost(100, 0.02) == pytest.approx(2.0 * 1.035)
    assert fee_buyer(100, 0.02) == pytest.approx(2.0 * 0.035)
    assert sell_proceeds(100, 0.02) == pytest.approx(2.0 * 0.965)
    assert fee_seller(100, 0.02) == pytest.approx(2.0 * 0.035)
