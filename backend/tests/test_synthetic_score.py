"""RED→GREEN: score/team_tier/minutaggio sintetici DETERMINISTICI (Fase 2b).

Segnaposto per dar vita al motore: nessuna pretesa di accuratezza, da sostituire
con statistiche reali (DECISIONS.md Fase 2b).
"""
from __future__ import annotations

from app.config.valuation_constants import SQUADRA_MAX, SQUADRA_MIN
from app.valuation.synthetic_score import (
    synthetic_minutaggio,
    synthetic_score,
    synthetic_team_tier,
)

ROLES = ["POR", "DIF", "CC", "ATT"]
IDS = [f"FIC{i:04d}" for i in range(1, 401)]


def test_score_deterministic():
    assert synthetic_score("ATT", "FIC0001") == synthetic_score("ATT", "FIC0001")


def test_score_in_range():
    for r in ROLES:
        for pid in IDS[:50]:
            s = synthetic_score(r, pid)
            assert 0.5 <= s <= 2.0


def test_score_mean_around_one():
    vals = [synthetic_score("CC", pid) for pid in IDS]
    mean = sum(vals) / len(vals)
    assert 0.90 <= mean <= 1.10


def test_score_has_spread():
    """Non tutti uguali: ci sono stelle (>1.4) e riserve (<0.8)."""
    vals = [synthetic_score("ATT", pid) for pid in IDS]
    assert any(v > 1.4 for v in vals)
    assert any(v < 0.8 for v in vals)


def test_team_tier_deterministic_and_in_band():
    for tid in ["inter", "juventus", "venezia", "como"]:
        f = synthetic_team_tier(tid)
        assert synthetic_team_tier(tid) == f
        assert SQUADRA_MIN <= f <= SQUADRA_MAX


def test_minutaggio_deterministic_and_in_range():
    for pid in IDS[:50]:
        m = synthetic_minutaggio(pid)
        assert synthetic_minutaggio(pid) == m
        assert 0.3 <= m <= 1.0
