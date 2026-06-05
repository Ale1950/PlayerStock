"""RED→GREEN: mercato% da net order flow (bucket volume → MARKET_DRIVERS)."""
from __future__ import annotations

import pytest

from app.market.market_pct import market_pct_from_net


def test_no_flow_no_move():
    assert market_pct_from_net(0) == 0.0


def test_buy_buckets():
    assert market_pct_from_net(3) == pytest.approx(0.012)    # 1-5
    assert market_pct_from_net(15) == pytest.approx(0.020)   # 6-20
    assert market_pct_from_net(50) == pytest.approx(0.025)   # >20


def test_sell_buckets_mirror():
    assert market_pct_from_net(-3) == pytest.approx(-0.012)
    assert market_pct_from_net(-15) == pytest.approx(-0.020)
    assert market_pct_from_net(-50) == pytest.approx(-0.025)
