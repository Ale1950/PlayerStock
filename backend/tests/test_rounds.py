"""Prezzo guidato dalla performance (D10): feed a innesto + round runner.

- feed sintetico deterministico, selezionato da config;
- run_round muove il PREZZO EQUO (ancora), NON la deviazione di trading;
- gli eventi per-round SOMMANO nelle stat stagionali mostrate (unica fonte);
- clamp RANGE_CLAMP rispettato anche con gain alto; market_state avanza.
"""
from __future__ import annotations

import pytest
from bson import ObjectId

from app.config.pricing_constants import RANGE_CLAMP
from app.market.rounds import run_round, seed_previous_season
from app.pricing.feed import SyntheticPerformanceProvider, get_performance_feed
from app.valuation.synthetic_stats import season_stats_of

FEED = SyntheticPerformanceProvider()


def _athlete(role="ATT", score=1.6, **extra):
    base = {
        "_id": ObjectId(), "sport_id": "calcio", "status": "ACTIVE", "role": role,
        "source_external_id": str(ObjectId()), "display_label": "X. Test",
        "score_performance": score, "minutaggio_pct": 0.95,
        "prezzo_iniziale_eur": 10.0, "prezzo_equo_eur": 10.0, "prezzo_corrente_eur": 10.0,
        "deviazione": 0.0,
    }
    base.update(extra)
    return base


# ── feed a innesto ──
def test_feed_deterministic_and_pluggable():
    a = _athlete()
    r1 = FEED.round_performance(a, 3)
    r2 = FEED.round_performance(a, 3)
    assert r1.perf == r2.perf and r1.stats == r2.stats
    assert get_performance_feed(None).name == "synthetic"

    class S:
        PERFORMANCE_FEED = "qualcosa-di-ignoto"
    assert get_performance_feed(S()).name == "synthetic"  # fallback mai dati reali


# ── run_round muove l'ancora, non la deviazione ──
@pytest.mark.asyncio
async def test_run_round_moves_equo_not_deviation(mock_db):
    docs = [_athlete(role=r, score=1.8) for _ in range(5) for r in ("ATT", "CC", "DIF", "POR")]
    await mock_db.athletes.insert_many(docs)
    rep = await run_round(mock_db, feed=FEED, gain=2.5)
    assert rep["round"] == 1 and rep["athletes"] == 20

    moved = 0
    for d in await mock_db.athletes.find({}).to_list(length=100):
        assert d["deviazione"] == 0.0                      # deviazione INTATTA
        if d["prezzo_equo_eur"] != 10.0:
            moved += 1
            # prezzo corrente ricomposto = equo (deviazione 0)
            assert d["prezzo_corrente_eur"] == pytest.approx(d["prezzo_equo_eur"])
    assert moved > 0                                        # qualcuno si è mosso
    st = await mock_db.market_state.find_one({"_id": "market"})
    assert st["current_round"] == 1


# ── eventi per-round SOMMANO nelle stat mostrate ──
@pytest.mark.asyncio
async def test_round_events_sum_to_season_stats(mock_db):
    a = _athlete(role="ATT", score=2.0)
    await mock_db.athletes.insert_one(a)
    for _ in range(8):
        await run_round(mock_db, feed=FEED, gain=1.0)

    evs = await mock_db.round_events.find({"athlete_id": a["_id"]}).to_list(length=100)
    assert len(evs) == 8
    exp_gol = sum(e["stats"]["gol"] for e in evs)
    exp_pres = sum(e["stats"]["presenze"] for e in evs)
    doc = await mock_db.athletes.find_one({"_id": a["_id"]})
    se = season_stats_of(doc)
    assert se["gol"] == exp_gol
    assert se["presenze"] == exp_pres


# ── clamp rispettato anche con gain alto ──
@pytest.mark.asyncio
async def test_clamp_respected_with_high_gain(mock_db):
    docs = [_athlete(role=r, score=2.0) for _ in range(5) for r in ("ATT", "CC", "DIF", "POR")]
    await mock_db.athletes.insert_many(docs)
    await run_round(mock_db, feed=FEED, gain=10.0)          # gain esagerato
    for e in await mock_db.round_events.find({}).to_list(length=100):
        # nessun round event supera il clamp del proprio ruolo
        ev_doc = await mock_db.athletes.find_one({"_id": e["athlete_id"]})
        rng = RANGE_CLAMP[ev_doc["role"]]
        assert rng["down"] - 1e-9 <= e["perf_pct"] <= rng["up"] + 1e-9


@pytest.mark.asyncio
async def test_seed_previous_season_builds_history(mock_db):
    await mock_db.athletes.insert_many([_athlete(role="ATT", score=1.7) for _ in range(6)])
    rep = await seed_previous_season(mock_db, feed=FEED, rounds=10, gain=2.0)
    assert rep["seeded_rounds"] == 10 and rep["final_round"] == 10
    st = await mock_db.market_state.find_one({"_id": "market"})
    assert st["current_round"] == 10
    # le stat stagionali si sono riempite
    doc = await mock_db.athletes.find_one({})
    assert season_stats_of(doc)["presenze"] >= 1
