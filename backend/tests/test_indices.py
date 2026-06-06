"""TDD: indici finanziari (puri) + bucketing adattivo per le serie equity/prezzo."""
from __future__ import annotations

import datetime as dt

import pytest

from app.economy.indices import (
    beta,
    bucket_points,
    choose_granularity,
    max_drawdown,
    pct_returns,
    portfolio_indices,
    sharpe_like,
    total_return_pct,
    volatility,
    win_rate,
)


def test_win_rate():
    orders = [{"side": "sell", "realized_pnl": 3.0}, {"side": "sell", "realized_pnl": -1.0}, {"side": "buy"}]
    assert win_rate(orders) == pytest.approx(50.0)
    assert win_rate([{"side": "buy"}]) is None  # nessuna vendita → n/d


def test_pct_returns():
    assert pct_returns([100, 110, 99]) == pytest.approx([0.1, -0.1])
    assert pct_returns([100]) == []


def test_total_return():
    assert total_return_pct([100, 110, 99]) == pytest.approx(-1.0)
    assert total_return_pct([]) is None


def test_volatility():
    assert volatility([100, 110, 99]) == pytest.approx(10.0)  # pstdev([0.1,-0.1])*100


def test_max_drawdown():
    assert max_drawdown([100, 110, 99]) == pytest.approx(-10.0)  # da picco 110 a 99
    assert max_drawdown([100, 90, 120]) == pytest.approx(-10.0)  # 100→90


def test_beta_self_is_one():
    m = [100, 110, 99]
    assert beta(m, m) == pytest.approx(1.0)


def test_beta_double_is_two():
    assert beta([100, 120, 96], [100, 110, 99]) == pytest.approx(2.0)


def test_sharpe_zero_vol_guarded():
    assert sharpe_like([100, 110, 121]) == 0.0  # vol 0 → niente segnale


def test_portfolio_indices_shape():
    ix = portfolio_indices([100, 110, 99], market=[100, 105, 100])
    assert set(ix) == {"return_pct", "volatility", "max_drawdown", "beta", "sharpe"}


# ───────── bucketing adattivo ─────────
def test_choose_granularity():
    assert choose_granularity("1S")[0] == "day"
    assert choose_granularity("1M")[0] == "day"
    assert choose_granularity("3M")[0] == "week"
    assert choose_granularity("all")[0] == "week"


def test_bucket_points_daily_last_value():
    base = dt.datetime(2026, 1, 1, 8, 0)
    pts = [
        {"ts": base, "value": 1.0},
        {"ts": base + dt.timedelta(hours=6), "value": 2.0},          # stesso giorno → vince l'ultimo
        {"ts": base + dt.timedelta(days=1), "value": 3.0},
    ]
    out = bucket_points(pts, "day")
    assert [p["value"] for p in out] == [2.0, 3.0]


def test_bucket_points_weekly():
    base = dt.datetime(2026, 1, 5)  # lunedì
    pts = [
        {"ts": base, "value": 1.0},
        {"ts": base + dt.timedelta(days=2), "value": 2.0},          # stessa settimana
        {"ts": base + dt.timedelta(days=8), "value": 5.0},          # settimana dopo
    ]
    out = bucket_points(pts, "week")
    assert [p["value"] for p in out] == [2.0, 5.0]
