"""RED→GREEN: lookup driver di pricing (da Gioco 5.xls / Serie 1)."""
from __future__ import annotations

import pytest

from app.pricing.drivers import band_count, band_minuti, band_voto_portiere, coeff


def test_band_minuti():
    assert band_minuti(80) == "GT_60"
    assert band_minuti(61) == "GT_60"
    assert band_minuti(60) == "BETWEEN_45_60"
    assert band_minuti(46) == "BETWEEN_45_60"
    assert band_minuti(45) == "LE_45"
    assert band_minuti(0) == "LE_45"


def test_band_count_three_state():
    # gol/assist: 0->ZERO, 1->ONE, >=2->GE_2
    assert band_count("GOL_FATTI", 0) == "ZERO"
    assert band_count("GOL_FATTI", 1) == "ONE"
    assert band_count("GOL_FATTI", 3) == "GE_2"


def test_band_count_ammonizione():
    assert band_count("AMMONIZIONE", 0) == "ZERO"
    assert band_count("AMMONIZIONE", 1) == "ONE"
    assert band_count("AMMONIZIONE", 2) == "TWO"
    assert band_count("AMMONIZIONE", 5) == "TWO"


def test_band_count_no_zero_band_returns_none():
    # eventi senza banda ZERO: count 0 -> nessun contributo
    assert band_count("ESPULSIONE", 0) is None
    assert band_count("RIGORI_SEGNATI", 0) is None
    assert band_count("RIGORI_PARATI", 0) is None
    assert band_count("AUTORETE", 0) is None
    assert band_count("RIGORI_SEGNATI", 1) == "ONE"
    assert band_count("RIGORI_SEGNATI", 3) == "THREE"
    assert band_count("AUTORETE", 3) == "GE_3"


def test_band_voto_portiere():
    assert band_voto_portiere(5.5) == "LT_6"
    assert band_voto_portiere(6.0) == "B6_7"
    assert band_voto_portiere(7.9) == "B6_7"
    assert band_voto_portiere(8.0) == "GE_8"


def test_coeff_matches_xls_values():
    # campioni verificati dall'xls
    assert coeff("GOL_FATTI", "ATT", "GE_2") == pytest.approx(0.0025)
    assert coeff("GOL_FATTI", "POR", "GE_2") == pytest.approx(0.0089)
    assert coeff("RIGORI_PARATI", "POR", "THREE") == pytest.approx(0.01)
    assert coeff("VOTO_PORTIERE", "POR", "GE_8") == pytest.approx(0.005)
    assert coeff("ESPULSIONE", "ATT", "ONE") == pytest.approx(-0.0075)
    assert coeff("MINUTI_GIOCATI", "DIF", "GT_60") == pytest.approx(0.0028)
