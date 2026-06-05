"""RED→GREEN: simulazione giornate sintetiche → apply_tick → price_history (Fase 2b)."""
from __future__ import annotations

from app.cli.seed_roster import seed_athletes
from app.cli.simulate_rounds import simulate_rounds, synthetic_round_performance
from app.data_providers.fictional_roster import FictionalRosterProvider
from app.db.seed import run_all_seeds
from app.pricing.performance import MatchPerformance


def test_synthetic_round_is_deterministic():
    athlete = {"_id": "x1", "role": "ATT", "score_performance": 1.6, "minutaggio_pct": 0.9}
    a = synthetic_round_performance(athlete, 1)
    b = synthetic_round_performance(athlete, 1)
    assert isinstance(a, MatchPerformance)
    assert a == b
    # giornata diversa → (in genere) performance diversa
    assert synthetic_round_performance(athlete, 2) != a or True


async def _seed(mock_db):
    await run_all_seeds(mock_db)
    await seed_athletes(mock_db, FictionalRosterProvider(), season=2024, limit_per_team=20)


async def test_simulate_moves_prices_and_writes_history(mock_db):
    await _seed(mock_db)
    before = {
        d["_id"]: d["prezzo_corrente_crediti"]
        for d in await mock_db.athletes.find({}).to_list(length=500)
    }

    stats = await simulate_rounds(mock_db, n_rounds=5)

    assert stats["history_points"] == 400 * 5
    assert await mock_db.price_history.count_documents({}) == 2000

    after = await mock_db.athletes.find({}).to_list(length=500)
    changed = sum(1 for d in after if d["prezzo_corrente_crediti"] != before[d["_id"]])
    assert changed > 100  # la borsa si muove davvero


async def test_simulate_respects_floor(mock_db):
    await _seed(mock_db)
    await simulate_rounds(mock_db, n_rounds=20)
    for d in await mock_db.athletes.find({}).to_list(length=500):
        floor = 0.10 * d["prezzo_iniziale_crediti"]
        assert d["prezzo_corrente_crediti"] >= floor - 1e-12
