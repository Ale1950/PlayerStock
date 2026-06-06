"""TDD: statistiche sportive sintetiche per giocatore/settimana.

Deterministiche, CONSISTENTI con lo score (alto→stat migliori) e col RUOLO
(ATT→gol, POR→parate). NON rigenerano lo score (l'economia tarata resta intatta).
"""
from __future__ import annotations

import pytest

from app.valuation.synthetic_stats import compact_weekly_stats, synthetic_weekly_stats


def test_deterministic():
    a = synthetic_weekly_stats(role="ATT", external_id="x1", score=1.4, minutaggio=0.9)
    b = synthetic_weekly_stats(role="ATT", external_id="x1", score=1.4, minutaggio=0.9)
    assert a == b


def test_structure():
    s = synthetic_weekly_stats(role="ATT", external_id="x2", score=1.2, minutaggio=0.9)
    assert set(s) == {"last_week", "season"}
    assert set(s["season"]) >= {"gol", "assist", "parate", "presenze", "minuti", "ammonizioni"}
    assert {"week", "minuti", "gol", "assist", "parate", "ammonizioni", "voto"} <= set(s["last_week"])


def test_role_gating_por_has_saves_not_goals():
    por = synthetic_weekly_stats(role="POR", external_id="g1", score=1.6, minutaggio=1.0)
    assert por["season"]["parate"] >= 1            # i portieri parano
    assert por["season"]["gol"] == 0               # e (quasi) mai segnano
    assert por["last_week"]["voto"] is not None     # voto portiere presente


def test_role_gating_att_no_saves():
    att = synthetic_weekly_stats(role="ATT", external_id="a1", score=1.6, minutaggio=1.0)
    assert att["last_week"]["parate"] is None        # i giocatori di movimento non parano
    assert att["season"]["parate"] == 0


def test_higher_score_means_more_goals():
    lo = synthetic_weekly_stats(role="ATT", external_id="same", score=0.6, minutaggio=1.0)
    hi = synthetic_weekly_stats(role="ATT", external_id="same", score=2.0, minutaggio=1.0)
    assert hi["season"]["gol"] >= lo["season"]["gol"]
    assert hi["season"]["gol"] > 0


def test_low_minutaggio_fewer_appearances():
    full = synthetic_weekly_stats(role="CC", external_id="m", score=1.0, minutaggio=1.0)
    bench = synthetic_weekly_stats(role="CC", external_id="m", score=1.0, minutaggio=0.3)
    assert full["season"]["presenze"] >= bench["season"]["presenze"]


def test_compact_from_doc():
    doc = {"role": "ATT", "source_external_id": "ext9", "score_performance": 1.5, "minutaggio_pct": 0.9}
    c = compact_weekly_stats(doc)
    assert set(c) >= {"gol", "assist", "presenze"}
    assert c["parate"] is None  # ATT
    por = compact_weekly_stats({"role": "POR", "source_external_id": "p9", "score_performance": 1.5, "minutaggio_pct": 1.0})
    assert por["parate"] is not None
