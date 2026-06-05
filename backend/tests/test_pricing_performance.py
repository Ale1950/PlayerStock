"""RED→GREEN: performance% settimanale (somma driver + clamp per ruolo)."""
from __future__ import annotations

import pytest

from app.pricing.performance import (
    MatchPerformance,
    clamp_perf,
    performance_pct,
    raw_performance_pct,
)


def test_raw_performance_attaccante():
    """ATT: 80', 1 gol, squadra subisce 1, 1 ammonizione, 1 assist."""
    perf = MatchPerformance(
        minuti=80, gol_fatti=1, gol_subiti=1, ammonizioni=1, assist=1
    )
    # 0.0045 + 0.0018 - 0.0015 - 0.0035 + 0.001 + (rig_sbagl ZERO 0.0)
    assert raw_performance_pct("ATT", perf) == pytest.approx(0.0023)


def test_raw_performance_portiere_clean_sheet():
    """POR: 90', clean sheet, 2 rigori parati, voto 8."""
    perf = MatchPerformance(minuti=90, gol_subiti=0, rigori_parati=2, voto=8.0)
    # 0.0018 + 0.0025 + 0.0078 + 0.005 + (ammon ZERO 0.0038)
    assert raw_performance_pct("POR", perf) == pytest.approx(0.0209)


def test_voto_portiere_ignored_for_outfield():
    perf = MatchPerformance(minuti=90, voto=9.0)
    p_att = raw_performance_pct("ATT", perf)
    perf_no_voto = MatchPerformance(minuti=90)
    assert p_att == pytest.approx(raw_performance_pct("ATT", perf_no_voto))


def test_clamp_perf_caps_to_role_range():
    assert clamp_perf("ATT", 0.05) == pytest.approx(0.0287)
    assert clamp_perf("ATT", -0.05) == pytest.approx(-0.0281)
    assert clamp_perf("DIF", -0.99) == pytest.approx(-0.0254)
    assert clamp_perf("POR", 0.99) == pytest.approx(0.0424)
    assert clamp_perf("CC", 0.01) == pytest.approx(0.01)  # dentro range -> invariato


def test_performance_pct_applies_clamp():
    # scenario che sfora il clamp ATT verso il basso
    perf = MatchPerformance(minuti=90, espulso=True, autoreti=3, rigori_sbagliati=2,
                            gol_subiti=2, ammonizioni=2)
    raw = raw_performance_pct("ATT", perf)
    assert raw < -0.0281  # sfora
    assert performance_pct("ATT", perf) == pytest.approx(-0.0281)
