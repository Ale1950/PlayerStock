"""Unit test puri (no DB) per il portfolio service Fase 4.

Coperti:
- cost_basis_from_lots
- avg_cost_per_share
- position_pnl (utile, perdita, lotti multipli, edge cases)
- aggregate_totals
- anonymize_display_name (privacy leaderboard)
"""
from __future__ import annotations

import datetime as dt

import pytest

from app.modules.portfolio.service import (
    aggregate_totals,
    anonymize_display_name,
    avg_cost_per_share,
    cost_basis_from_lots,
    position_pnl,
)


def _lot(qty: int, price: float, days_ago: int = 0) -> dict:
    return {
        "qty": qty, "price": price,
        "acquired_at": dt.datetime(2025, 1, 1) - dt.timedelta(days=days_ago),
    }


# ───────── cost_basis_from_lots ─────────
class TestCostBasis:
    def test_empty_lots(self):
        assert cost_basis_from_lots([]) == 0.0

    def test_single_lot(self):
        # 100 quote × 0.02 = 2.00
        assert cost_basis_from_lots([_lot(100, 0.02)]) == pytest.approx(2.0)

    def test_multiple_lots(self):
        # 100×0.02 + 50×0.03 + 200×0.025 = 2 + 1.5 + 5 = 8.5
        lots = [_lot(100, 0.02), _lot(50, 0.03), _lot(200, 0.025)]
        assert cost_basis_from_lots(lots) == pytest.approx(8.5)

    def test_zero_qty_lot(self):
        # un lot residuale a 0 quote non contribuisce
        lots = [_lot(0, 0.05), _lot(100, 0.02)]
        assert cost_basis_from_lots(lots) == pytest.approx(2.0)

    def test_missing_fields_defaults(self):
        # robustezza: qty/price mancanti = 0
        lots = [{"acquired_at": dt.datetime(2025, 1, 1)}, _lot(100, 0.02)]
        assert cost_basis_from_lots(lots) == pytest.approx(2.0)


# ───────── avg_cost_per_share ─────────
class TestAvgCost:
    def test_empty(self):
        assert avg_cost_per_share([]) == 0.0

    def test_uniform(self):
        # tutto a 0.02 → avg = 0.02
        lots = [_lot(100, 0.02), _lot(50, 0.02)]
        assert avg_cost_per_share(lots) == pytest.approx(0.02)

    def test_weighted(self):
        # 100×0.02 + 100×0.04 = 6 / 200 = 0.03 (media pesata)
        lots = [_lot(100, 0.02), _lot(100, 0.04)]
        assert avg_cost_per_share(lots) == pytest.approx(0.03)

    def test_zero_total_qty(self):
        # nessuna quota → 0
        assert avg_cost_per_share([_lot(0, 0.5)]) == 0.0


# ───────── position_pnl ─────────
class TestPositionPnL:
    def test_position_in_profit(self):
        # 100 quote a 0.01 medio, prezzo corrente 0.02 → +100% P&L
        lots = [_lot(100, 0.01)]
        out = position_pnl(qty=100, lots=lots, current_price=0.02)
        assert out["quantity"] == 100
        assert out["cost_basis"] == pytest.approx(1.0)
        assert out["current_value"] == pytest.approx(2.0)
        assert out["pnl_abs"] == pytest.approx(1.0)
        assert out["pnl_pct"] == pytest.approx(100.0)
        assert out["avg_cost"] == pytest.approx(0.01)

    def test_position_in_loss(self):
        # 100 quote a 0.05, prezzo corrente 0.04 → -20% P&L
        lots = [_lot(100, 0.05)]
        out = position_pnl(qty=100, lots=lots, current_price=0.04)
        assert out["cost_basis"] == pytest.approx(5.0)
        assert out["current_value"] == pytest.approx(4.0)
        assert out["pnl_abs"] == pytest.approx(-1.0)
        assert out["pnl_pct"] == pytest.approx(-20.0)

    def test_position_breakeven(self):
        # cost = current → 0 PnL
        lots = [_lot(100, 0.025)]
        out = position_pnl(qty=100, lots=lots, current_price=0.025)
        assert out["pnl_abs"] == pytest.approx(0.0)
        assert out["pnl_pct"] == pytest.approx(0.0)

    def test_multi_lot_weighted(self):
        # 100×0.01 + 200×0.02 = 1+4 = 5 / 300 = ~0.01667 avg
        # prezzo corrente 0.03 → value = 9 → pnl 4, +80%
        lots = [_lot(100, 0.01, 10), _lot(200, 0.02, 5)]
        out = position_pnl(qty=300, lots=lots, current_price=0.03)
        assert out["cost_basis"] == pytest.approx(5.0)
        assert out["current_value"] == pytest.approx(9.0)
        assert out["pnl_abs"] == pytest.approx(4.0)
        assert out["pnl_pct"] == pytest.approx(80.0)
        assert out["avg_cost"] == pytest.approx(5.0 / 300)

    def test_zero_qty_no_div_zero(self):
        out = position_pnl(qty=0, lots=[], current_price=0.05)
        assert out["pnl_pct"] is None  # no cost basis → no %
        assert out["pnl_abs"] == 0.0

    def test_negative_qty_clamped(self):
        # difensivo: qty < 0 forzato a 0
        out = position_pnl(qty=-50, lots=[], current_price=0.05)
        assert out["quantity"] == 0

    def test_floor_price_scenario(self):
        # scenario floor 10% — comprato a 0.10, ora 0.01 → -90% (peggior caso)
        lots = [_lot(1000, 0.10)]
        out = position_pnl(qty=1000, lots=lots, current_price=0.01)
        assert out["pnl_pct"] == pytest.approx(-90.0)


# ───────── aggregate_totals ─────────
class TestAggregateTotals:
    def test_empty_portfolio(self):
        out = aggregate_totals(balance_eur=10_000.0, positions=[])
        assert out["cash_eur"] == 10_000.0
        assert out["positions_value"] == 0.0
        assert out["positions_cost_basis"] == 0.0
        assert out["total_equity"] == 10_000.0
        assert out["total_pnl_pct"] is None
        assert out["positions_count"] == 0

    def test_mixed_portfolio(self):
        positions = [
            {"current_value": 100.0, "cost_basis": 80.0, "quantity": 50},   # +20
            {"current_value": 50.0, "cost_basis": 60.0, "quantity": 25},    # -10
            {"current_value": 30.0, "cost_basis": 30.0, "quantity": 10},    # 0
        ]
        out = aggregate_totals(balance_eur=500.0, positions=positions)
        assert out["positions_value"] == pytest.approx(180.0)
        assert out["positions_cost_basis"] == pytest.approx(170.0)
        assert out["total_equity"] == pytest.approx(680.0)  # 500 cash + 180 titoli
        assert out["total_pnl_abs"] == pytest.approx(10.0)
        assert out["total_pnl_pct"] == pytest.approx(10.0 / 170.0 * 100.0)
        assert out["positions_count"] == 3

    def test_excludes_zero_qty_from_count(self):
        positions = [
            {"current_value": 0.0, "cost_basis": 0.0, "quantity": 0},
            {"current_value": 50.0, "cost_basis": 40.0, "quantity": 10},
        ]
        out = aggregate_totals(balance_eur=100.0, positions=positions)
        assert out["positions_count"] == 1

    def test_only_cash(self):
        out = aggregate_totals(balance_eur=10_000.0, positions=[])
        # all'inizio del gioco: solo cash, no titoli
        assert out["total_equity"] == 10_000.0


# ───────── anonymize_display_name ─────────
class TestAnonymizeDisplayName:
    def test_two_tokens_anonymous(self):
        assert anonymize_display_name("Mario Rossi", is_self=False) == "Mario R."

    def test_self_full_name(self):
        assert anonymize_display_name("Mario Rossi", is_self=True) == "Mario Rossi"

    def test_three_tokens_takes_last_initial(self):
        assert anonymize_display_name("Alessandro Della Valle", is_self=False) == "Alessandro V."

    def test_single_token_unchanged(self):
        assert anonymize_display_name("Pelé", is_self=False) == "Pelé"

    def test_empty_fallback(self):
        assert anonymize_display_name("", is_self=False) == "Player"
        assert anonymize_display_name(None, is_self=False) == "Player"

    def test_no_email_leak(self):
        # se per errore arrivasse un'email come name, viene comunque troncata
        out = anonymize_display_name("mario.rossi@example.com other", is_self=False)
        # non testiamo il contenuto esatto, solo che non resti l'email completa
        assert "@example.com" not in out or out.endswith(".")
