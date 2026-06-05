"""Test idempotenza seed.

run_all_seeds() usa update_one(..., upsert=True): eseguirlo N volte deve
lasciare il DB nello stesso stato (nessun duplicato). Verifichiamo anche il
pattern di upsert usato da seed_roster per gli atleti (stessa chiave -> 1 doc).

Usa mongomock-motor: nessuna connessione ad Atlas.
"""
from __future__ import annotations

from app.config.teams_fantasy_map import SERIE_A_FANTASY_MAP
from app.db.seed import run_all_seeds
from app.models.common import utc_now


async def test_run_all_seeds_is_idempotent(mock_db):
    # primo run
    await run_all_seeds(mock_db)
    sports_1 = await mock_db.sports.count_documents({})
    teams_1 = await mock_db.teams_fantasy.count_documents({})

    assert sports_1 == 4  # calcio + tennis + basket + f1
    assert teams_1 == len(SERIE_A_FANTASY_MAP) == 20

    # secondo run: stesso stato, nessun duplicato
    await run_all_seeds(mock_db)
    sports_2 = await mock_db.sports.count_documents({})
    teams_2 = await mock_db.teams_fantasy.count_documents({})

    assert sports_2 == sports_1
    assert teams_2 == teams_1


async def test_athlete_upsert_is_idempotent(mock_db):
    """Stesso pattern di seed_roster: upsert con chiave naturale -> 1 solo doc."""
    now = utc_now()
    key = {"sport_id": "calcio", "internal_full_name": "Lautaro Martinez", "team_fantasy_id": "t1"}
    doc = {**key, "display_label": "L. Martinez", "status": "ACTIVE"}

    for _ in range(3):
        await mock_db.athletes.update_one(
            key,
            {"$set": {**doc, "updated_at": now}, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )

    count = await mock_db.athletes.count_documents(key)
    assert count == 1


async def test_seed_then_count_roster_target(mock_db):
    """20 squadre seedate -> target roster 400 (20 atleti/squadra)."""
    await run_all_seeds(mock_db)
    teams = await mock_db.teams_fantasy.count_documents({"sport_id": "calcio"})
    assert teams == 20
    assert teams * 20 == 400  # float roster atteso da `seed_roster --limit 20`
