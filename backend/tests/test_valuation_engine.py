"""RED→GREEN: valuation engine (valore iniziale + prezzo iniziale, banda calibrata)."""
from __future__ import annotations

import pytest

from app.config.pricing_constants import FLOAT_AZIONI_PER_GIOCATORE
from app.config.valuation_constants import BASE_RUOLO, K_GLOBAL, SQUADRA_MAX, SQUADRA_MIN
from app.valuation.engine import prezzo_iniziale, valuation


ROLES = ["POR", "DIF", "CC", "ATT"]


def test_valuation_neutral_per_role_equals_base_times_k():
    """Neutro = score 1.0, età picco (25), minutaggio pieno, squadra media (1.0)."""
    for r in ROLES:
        v = valuation(role=r, score=1.0, eta=25, minutaggio_pct=1.0, fattore_squadra=1.0)
        assert v == pytest.approx(K_GLOBAL * BASE_RUOLO[r])


def test_valuation_neutral_average_is_base_value():
    """Media sui ruoli del neutro ≈ base intrinseca dell'engine (K_GLOBAL).

    NB: engine LEGACY (Cr). Dalla migrazione € (D7) NON guida più il prezzo: l'ancora
    è `market_value_eur_seed / FLOAT` (Opzione B). Test sul comportamento intrinseco.
    """
    vals = [valuation(role=r, score=1.0, eta=25, minutaggio_pct=1.0, fattore_squadra=1.0)
            for r in ROLES]
    assert sum(vals) / len(vals) == pytest.approx(K_GLOBAL)


def test_prezzo_iniziale_is_valore_over_float():
    v = valuation(role="CC", score=1.0, eta=25, minutaggio_pct=1.0, fattore_squadra=1.0)
    assert prezzo_iniziale(role="CC", score=1.0, eta=25, minutaggio_pct=1.0,
                           fattore_squadra=1.0) == pytest.approx(v / FLOAT_AZIONI_PER_GIOCATORE)


def test_extremes_within_decided_price_band():
    """Spread ~8x: stella ATT giovane top ~0.030–0.040, riserva POR ~0.005–0.010."""
    top = prezzo_iniziale(role="ATT", score=2.0, eta=20, minutaggio_pct=1.0,
                          fattore_squadra=SQUADRA_MAX)
    bottom = prezzo_iniziale(role="POR", score=0.5, eta=37, minutaggio_pct=0.1,
                             fattore_squadra=SQUADRA_MIN)
    assert 0.005 <= bottom <= 0.010
    assert 0.030 <= top <= 0.040
    assert top > bottom


def test_score_is_clamped_low():
    """Score sotto il minimo di valuation non sfonda il floor della banda."""
    v_very_low = valuation(role="POR", score=0.1, eta=37, minutaggio_pct=0.1, fattore_squadra=0.92)
    assert v_very_low / FLOAT_AZIONI_PER_GIOCATORE >= 0.005
