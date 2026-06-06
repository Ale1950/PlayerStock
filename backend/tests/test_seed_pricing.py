"""RED→GREEN: il seed cabla il valuation engine → prezzi iniziali VARIATI (Fase 2b)."""
from __future__ import annotations

from app.cli.seed_roster import seed_athletes
from app.data_providers.fictional_roster import FictionalRosterProvider
from app.db.seed import run_all_seeds


async def test_seed_prices_are_varied_and_in_band(mock_db):
    await run_all_seeds(mock_db)
    await seed_athletes(mock_db, FictionalRosterProvider(), season=2024, limit_per_team=20)

    docs = await mock_db.athletes.find({}).to_list(length=500)
    prices = [d["prezzo_iniziale_eur"] for d in docs]

    assert len(prices) == 400
    assert len(set(prices)) > 50                      # non tutti uguali
    assert all(0.4 <= p <= 120.0 for p in prices)     # banda € (D7: ancora €M / 1M)
    assert max(prices) - min(prices) > 1.0            # spread reale in €


async def test_seed_writes_audit_fields(mock_db):
    await run_all_seeds(mock_db)
    await seed_athletes(mock_db, FictionalRosterProvider(), season=2024, limit_per_team=20)

    d = await mock_db.athletes.find_one({})
    assert "score_performance" in d
    assert "fattore_squadra" in d
    assert 0.5 <= d["score_performance"] <= 2.0
    assert d["prezzo_corrente_eur"] == d["prezzo_iniziale_eur"]
    assert d["prezzo_iniziale_eur"] == d["valore_iniziale_eur"] / 1_000_000


async def test_seed_initializes_primary_pool(mock_db):
    """Float intero in emissione primaria (IPO): pool = float, circolante = 0."""
    await run_all_seeds(mock_db)
    await seed_athletes(mock_db, FictionalRosterProvider(), season=2024, limit_per_team=20)
    d = await mock_db.athletes.find_one({})
    assert d["primary_pool_qty"] == 1_000_000
    assert d["circulating_qty"] == 0
    assert d["primary_pool_qty"] + d["circulating_qty"] == d["float_quote"]
