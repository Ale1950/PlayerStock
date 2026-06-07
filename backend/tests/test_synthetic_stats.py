"""Stat MOSTRATE = lettore dell'accumulo round (unica fonte, D10).

synthetic_stats non genera più: legge `season_stats` / `last_round_stats` dal doc atleta.
"""
from __future__ import annotations

from app.valuation.synthetic_stats import (
    compact_weekly_stats,
    last_round_of,
    season_stats_of,
    synthetic_weekly_stats,
)


def test_empty_athlete_zeros_and_structure():
    a = {"role": "ATT"}
    s = synthetic_weekly_stats(a)
    assert set(s.keys()) == {"last_week", "season"}
    assert s["season"]["gol"] == 0 and s["season"]["presenze"] == 0


def test_reads_stored_season_stats():
    a = {"role": "ATT", "season_stats": {"presenze": 9, "minuti": 760, "gol": 7,
                                         "assist": 3, "ammonizioni": 2, "parate": 0}}
    se = season_stats_of(a)
    assert se["gol"] == 7 and se["assist"] == 3 and se["presenze"] == 9


def test_compact_por_has_saves_outfield_none():
    por = compact_weekly_stats({"role": "POR", "season_stats": {"parate": 14, "gol": 0}})
    assert por["parate"] == 14
    att = compact_weekly_stats({"role": "ATT", "season_stats": {"gol": 5, "parate": 0}})
    assert att["parate"] is None and att["gol"] == 5


def test_last_round_reads_stored():
    a = {"role": "ATT", "last_round_stats": {"minuti": 90, "gol": 2, "assist": 0,
                                             "parate": None, "ammonizioni": 0, "voto": None}}
    assert last_round_of(a)["gol"] == 2


def test_last_round_default_when_missing():
    lr = last_round_of({"role": "POR"})
    assert lr["gol"] == 0 and lr["parate"] == 0   # POR default parate=0
    assert last_round_of({"role": "ATT"})["parate"] is None
