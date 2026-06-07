"""Prezzo su SORPRESA = reale − atteso (FISSO). Golden invariato (cambia la mappatura).

- E[sorpresa] ≈ 0 sul GENERATORE REALE (atteso campionato con lo stesso feed, incl.
  effetto-squadra gol-subiti);
- un giocatore che rende ESATTAMENTE come da attese → prezzo ~fermo.
"""
from __future__ import annotations

import pytest
from bson import ObjectId

from app.pricing.feed import (
    RoundResult,
    SyntheticPerformanceProvider,
    expected_perf_pct,
)
from app.pricing.performance import MatchPerformance, raw_performance_pct, surprise_pct

FEED = SyntheticPerformanceProvider()


def test_expected_makes_surprise_mean_zero_real_generator():
    """Media della sorpresa sui round live (indici disgiunti dal campione atteso) ≈ 0."""
    for role in ("ATT", "CC", "DIF", "POR"):
        a = {"role": role, "source_external_id": f"sx-{role}",
             "score_performance": 1.4, "minutaggio_pct": 0.9}
        exp = expected_perf_pct(a, k=400)
        surprises = [
            raw_performance_pct(role, FEED.round_performance(a, r).perf) - exp
            for r in range(1, 801)               # round live 1..800 (≠ range campione 900k)
        ]
        mean = sum(surprises) / len(surprises)
        assert abs(mean) < 1e-3, (role, mean)    # ≈ 0 sul generatore reale


@pytest.mark.asyncio
async def test_constant_player_is_flat(mock_db):
    """Giocatore che rende come da attese (feed costante) → prezzo fermo (sorpresa 0)."""
    from app.market.rounds import run_round

    fixed = MatchPerformance(minuti=90, gol_fatti=1, assist=0, gol_subiti=1)

    class ConstFeed:
        name = "const"

        def round_performance(self, athlete, round_idx):
            return RoundResult(perf=fixed, stats={"presenze": 1, "minuti": 90, "gol": 1,
                                                  "assist": 0, "parate": None, "ammonizioni": 0,
                                                  "voto": None})

    a = {"_id": ObjectId(), "sport_id": "calcio", "status": "ACTIVE", "role": "ATT",
         "prezzo_iniziale_eur": 10.0, "prezzo_equo_eur": 10.0, "prezzo_corrente_eur": 10.0,
         "deviazione": 0.0,
         # atteso = ESATTAMENTE il raw del rendimento costante → sorpresa 0
         "expected_perf_pct": raw_performance_pct("ATT", fixed)}
    await mock_db.athletes.insert_one(a)
    for _ in range(15):
        await run_round(mock_db, feed=ConstFeed(), gain=2.5)

    d = await mock_db.athletes.find_one({"_id": a["_id"]})
    assert d["prezzo_equo_eur"] == pytest.approx(10.0)       # fermo: nessuna deriva
    assert d["prezzo_corrente_eur"] == pytest.approx(10.0)


def test_surprise_pct_helper_clamps():
    # sorpresa enorme resta dentro il clamp del ruolo (ATT up +0.0287)
    big = surprise_pct("ATT", raw_actual=0.5, expected=0.0, gain=10.0)
    assert big == pytest.approx(0.0287)
    # rendimento = atteso → 0
    assert surprise_pct("ATT", raw_actual=0.004, expected=0.004) == 0.0
