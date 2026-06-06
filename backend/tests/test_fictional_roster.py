"""Test roster fittizio (Decisione Fase 1 — Opzione 3 raffinata).

~400 giocatori FITTIZI ma realistici (nessuna persona reale), file seed statico
nel repo, schema normalizzato identico a quello del provider Football-Data.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict

from bson import ObjectId

from app.data_providers.fictional_roster import (
    ROSTER_JSON_PATH,
    FictionalRosterProvider,
    generate_roster,
)
from app.models.athlete import AthletePublic


def test_generate_roster_returns_400():
    assert len(generate_roster()) == 400


def test_role_distribution_per_team():
    """20 squadre × (2 POR + 6 DIF + 6 CC + 6 ATT) = 400."""
    roster = generate_roster()
    by_team: dict[str, Counter] = defaultdict(Counter)
    for p in roster:
        by_team[p["team_fd_id"]][p["role"]] += 1
    assert len(by_team) == 20
    for counts in by_team.values():
        assert counts == Counter({"POR": 2, "DIF": 6, "CC": 6, "ATT": 6})


def test_generate_roster_is_deterministic():
    assert generate_roster(123) == generate_roster(123)


def test_player_fields_valid():
    for p in generate_roster():
        assert p["internal_full_name"].strip()
        assert len(p["nationality_iso3"]) == 3
        assert p["role"] in {"POR", "DIF", "CC", "ATT"}
        assert 16 <= p["age"] <= 42
        assert p["external_id"]
        assert p["team_fd_name"]
        assert p["team_fd_id"]


def test_names_are_unique():
    names = [p["internal_full_name"] for p in generate_roster()]
    assert len(names) == len(set(names))


def test_committed_json_exists_and_valid():
    """Il file seed statico nel repo deve esistere con 400 entry valide."""
    data = json.loads(ROSTER_JSON_PATH.read_text(encoding="utf-8"))
    assert len(data) == 400
    by_team: dict[str, Counter] = defaultdict(Counter)
    for p in data:
        by_team[p["team_fd_id"]][p["role"]] += 1
    assert len(by_team) == 20


async def test_provider_fetch_serie_a_full_normalized():
    """FictionalRosterProvider legge il file statico, schema = fetch_serie_a_full."""
    prov = FictionalRosterProvider()
    players = await prov.fetch_serie_a_full(season=2024)
    assert len(players) == 400
    sample = players[0]
    for key in ("external_id", "internal_full_name", "role", "nationality_iso3", "age", "team_fd_name"):
        assert key in sample


async def test_provider_health_check_ok():
    prov = FictionalRosterProvider()
    health = await prov.health_check()
    assert health["ok"] is True
    assert health["count"] == 400


async def test_seed_athletes_populates_400(mock_db):
    """Seeding fittizio su mongomock → 400 atleti, display L2 presente."""
    from app.cli.seed_roster import seed_athletes
    from app.db.seed import run_all_seeds

    await run_all_seeds(mock_db)
    stats = await seed_athletes(
        mock_db, FictionalRosterProvider(), season=2024, limit_per_team=20
    )

    count = await mock_db.athletes.count_documents({"sport_id": "calcio"})
    assert count == 400
    assert stats["items_synced"] == 400
    assert stats["skipped_no_team"] == 0

    doc = await mock_db.athletes.find_one({})
    assert doc["display_label"]
    assert doc["display_initial"]
    assert doc["data_source"] == "fictional_roster"


async def test_seed_athletes_is_idempotent(mock_db):
    """Re-run del seeding → sempre 400 atleti (upsert, nessun duplicato)."""
    from app.cli.seed_roster import seed_athletes
    from app.db.seed import run_all_seeds

    await run_all_seeds(mock_db)
    prov = FictionalRosterProvider()
    await seed_athletes(mock_db, prov, season=2024, limit_per_team=20)
    await seed_athletes(mock_db, prov, season=2024, limit_per_team=20)

    count = await mock_db.athletes.count_documents({"sport_id": "calcio"})
    assert count == 400


def test_athlete_public_never_exposes_internal_full_name():
    """Cancello 1: nessun internal_full_name nelle response (anonimizzazione L2)."""
    doc = {
        "_id": ObjectId(),
        "sport_id": "calcio",
        "internal_full_name": "Mario Rossi",  # DEVE sparire
        "display_initial": "M.",
        "display_lastname": "Rossi",
        "display_label": "M. Rossi",
        "nationality_iso3": "ITA",
        "role": "ATT",
        "age": 25,
        "team_fantasy_id": ObjectId(),
        "valore_iniziale_eur": 10000.0,
        "float_quote": 1_000_000,
        "prezzo_iniziale_eur": 0.01,
        "prezzo_corrente_eur": 0.01,
        "status": "ACTIVE",
    }
    dumped = AthletePublic.model_validate(doc).model_dump()
    assert "internal_full_name" not in dumped
    assert dumped["display_label"] == "M. Rossi"
