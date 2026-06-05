"""RED→GREEN: il seed cabla il valuation engine → prezzi iniziali VARIATI (Fase 2b)."""
from __future__ import annotations

from app.cli.seed_roster import seed_athletes
from app.data_providers.fictional_roster import FictionalRosterProvider
from app.db.seed import run_all_seeds


async def test_seed_prices_are_varied_and_in_band(mock_db):
    await run_all_seeds(mock_db)
    await seed_athletes(mock_db, FictionalRosterProvider(), season=2024, limit_per_team=20)

    docs = await mock_db.athletes.find({}).to_list(length=500)
    prices = [d["prezzo_iniziale_crediti"] for d in docs]

    assert len(prices) == 400
    assert len(set(prices)) > 50                      # non tutti uguali a 0.01
    assert all(0.005 <= p <= 0.050 for p in prices)   # dentro la banda decisa
    assert max(prices) - min(prices) > 0.01           # spread reale


async def test_seed_writes_audit_fields(mock_db):
    await run_all_seeds(mock_db)
    await seed_athletes(mock_db, FictionalRosterProvider(), season=2024, limit_per_team=20)

    d = await mock_db.athletes.find_one({})
    assert "score_performance" in d
    assert "fattore_squadra" in d
    assert 0.5 <= d["score_performance"] <= 2.0
    assert d["prezzo_corrente_crediti"] == d["prezzo_iniziale_crediti"]
    assert d["prezzo_iniziale_crediti"] == d["valore_iniziale_crediti"] / 1_000_000
