"""RED→GREEN: valuation engine (valore iniziale + prezzo iniziale, banda calibrata)."""
from __future__ import annotations

import pytest

from app.config.pricing_constants import (
    FLOAT_AZIONI_PER_GIOCATORE,
    VALORE_BASE_GIOCATORE_CREDITI,
)
from app.config.valuation_constants import BASE_RUOLO, K_GLOBAL
from app.valuation.engine import prezzo_iniziale, valuation


ROLES = ["POR", "DIF", "CC", "ATT"]


def test_valuation_neutral_per_role_equals_base_times_k():
    """Neutro = score 1.0, età picco (25), minutaggio pieno, squadra media (1.0)."""
    for r in ROLES:
        v = valuation(role=r, score=1.0, eta=25, minutaggio_pct=1.0, fattore_squadra=1.0)
        assert v == pytest.approx(K_GLOBAL * BASE_RUOLO[r])


def test_valuation_neutral_average_is_base_value():
    """Media sui ruoli del neutro ≈ valore base (10.000) → prezzo ≈ 0.01."""
    vals = [valuation(role=r, score=1.0, eta=25, minutaggio_pct=1.0, fattore_squadra=1.0)
            for r in ROLES]
    assert sum(vals) / len(vals) == pytest.approx(VALORE_BASE_GIOCATORE_CREDITI)


def test_prezzo_iniziale_is_valore_over_float():
    v = valuation(role="CC", score=1.0, eta=25, minutaggio_pct=1.0, fattore_squadra=1.0)
    assert prezzo_iniziale(role="CC", score=1.0, eta=25, minutaggio_pct=1.0,
                           fattore_squadra=1.0) == pytest.approx(v / FLOAT_AZIONI_PER_GIOCATORE)


def test_extremes_within_decided_price_band():
    """Estremi ATT-top-giovane / POR-scarso-anziano dentro ~0.005–0.050."""
    top = prezzo_iniziale(role="ATT", score=2.0, eta=25, minutaggio_pct=1.0, fattore_squadra=1.20)
    bottom = prezzo_iniziale(role="POR", score=0.5, eta=37, minutaggio_pct=0.1, fattore_squadra=0.92)
    assert 0.005 <= bottom <= 0.050
    assert 0.005 <= top <= 0.050
    assert top > bottom


def test_score_is_clamped_low():
    """Score sotto il minimo di valuation non sfonda il floor della banda."""
    v_very_low = valuation(role="POR", score=0.1, eta=37, minutaggio_pct=0.1, fattore_squadra=0.92)
    assert v_very_low / FLOAT_AZIONI_PER_GIOCATORE >= 0.005
