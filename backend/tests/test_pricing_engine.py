"""RED→GREEN: tick di prezzo (1 + perf% + mkt% + eng%), floor 10%, piena precisione."""
from __future__ import annotations

import pytest

from app.config.pricing_constants import FLOOR_PCT_PREZZO_INIZIALE
from app.pricing.engine import apply_tick


def test_tick_applies_performance():
    res = apply_tick(prezzo_corrente=0.01, prezzo_iniziale=0.01, perf_pct=0.0023)
    assert res.new_price == pytest.approx(0.01 * 1.0023)
    assert res.pct_change == pytest.approx(0.0023)
    assert res.floored is False


def test_tick_full_internal_precision_not_rounded_to_4dp():
    # variazione piccola su prezzo basso: il prezzo interno NON è arrotondato a 4 decimali
    res = apply_tick(prezzo_corrente=0.006, prezzo_iniziale=0.01, perf_pct=0.001)
    assert res.new_price == pytest.approx(0.006 * 1.001)  # 0.006006
    assert res.new_price != round(res.new_price, 4)


def test_tick_floor_at_10pct_of_initial():
    res = apply_tick(prezzo_corrente=0.0011, prezzo_iniziale=0.01, perf_pct=-0.5)
    floor = FLOOR_PCT_PREZZO_INIZIALE * 0.01  # 0.001
    assert res.new_price == pytest.approx(floor)
    assert res.floored is True
    assert res.pct_change == pytest.approx((floor - 0.0011) / 0.0011)


def test_tick_no_upper_cap():
    res = apply_tick(prezzo_corrente=0.01, prezzo_iniziale=0.01, perf_pct=0.0287)
    assert res.new_price == pytest.approx(0.010287)
    assert res.floored is False


def test_tick_combines_market_and_engagement():
    res = apply_tick(prezzo_corrente=0.02, prezzo_iniziale=0.01,
                     perf_pct=0.01, mercato_pct=0.005, engagement_pct=0.002)
    assert res.new_price == pytest.approx(0.02 * (1 + 0.017))
