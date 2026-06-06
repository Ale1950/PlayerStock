"""Guardrail IP: pool ripuliti dai big noti + rename in-place deterministico per-ID.

- Pool senza token distintivi di calciatori reali attuali.
- regenerate_name: deterministico (stesso ID ⇒ stesso nome), per-nazionalità,
  evita collisioni, mai un token bandito.
- CLI: rinomina SOLO i nomi che echeggiano big reali, tocca SOLO i campi nome,
  lascia tutto il resto intatto; idempotente (seconda passata = nessun cambio).
"""
from __future__ import annotations

import pytest

from app.data_providers.fictional_roster import (
    BANNED_REAL_PLAYER_TOKENS,
    NAME_POOLS,
    regenerate_name,
)


# ───────────────────── pool ripuliti ─────────────────────
def test_pools_have_no_banned_real_player_tokens():
    for nat, pool in NAME_POOLS.items():
        toks = set(pool["first"]) | set(pool["last"])
        bad = toks & BANNED_REAL_PLAYER_TOKENS
        assert not bad, f"{nat} contiene token vietati: {bad}"


def test_pools_unchanged_size_and_no_empties():
    for nat, pool in NAME_POOLS.items():
        assert len(pool["first"]) >= 15, nat
        assert len(pool["last"]) >= 15, nat


# ───────────────────── regenerate_name ─────────────────────
def test_regenerate_deterministic_per_id():
    a = regenerate_name("ARG", "FIC0197")
    b = regenerate_name("ARG", "FIC0197")
    assert a == b


def test_regenerate_is_nationality_coherent():
    name = regenerate_name("HRV", "FIC0022")
    first, last = name.split(" ", 1)
    assert first in NAME_POOLS["HRV"]["first"]
    assert last in NAME_POOLS["HRV"]["last"]


def test_regenerate_never_yields_banned_token():
    for nat in NAME_POOLS:
        for i in range(50):
            name = regenerate_name(nat, f"{nat}-{i}")
            assert not (set(name.split()) & BANNED_REAL_PLAYER_TOKENS)


def test_regenerate_avoids_used_names():
    # satura quasi tutto il pool ARG come "usato" e verifica che eviti le collisioni
    used = {regenerate_name("ARG", f"k{i}") for i in range(5)}
    fresh = regenerate_name("ARG", "knew", used_names=used)
    assert fresh not in used


# ───────────────────── CLI in-place ─────────────────────
def _athlete(ext, name, nat, team, **extra):
    base = {
        "sport_id": "calcio", "status": "ACTIVE", "team_fantasy_id": team,
        "source_external_id": ext, "internal_full_name": name, "nationality_iso3": nat,
        "role": "ATT", "score_performance": 1.0, "fattore_squadra": 1.0,
        "float_quote": 1_000_000, "primary_pool_qty": 1_000_000, "circulating_qty": 0,
        "prezzo_iniziale_eur": 0.01, "prezzo_corrente_eur": 0.01,
        "valore_iniziale_eur": 10_000.0,
        "display_initial": name[0] + ".", "display_lastname": name.split()[-1],
        "display_label": f"{name[0]}. {name.split()[-1]}",
    }
    base.update(extra)
    return base


@pytest.mark.asyncio
async def test_cli_renames_only_echoes_and_preserves_everything(mock_db):
    from app.cli.rename_real_player_echoes import rename_real_player_echoes

    docs = [
        _athlete("FIC0197", "Lautaro Acosta", "ARG", "tA"),     # echo → rinominare
        _athlete("FIC0022", "Domagoj Knezevic", "HRV", "tB"),   # echo → rinominare
        _athlete("FIC0003", "Salvatore Ricci", "ITA", "tA"),    # ok → invariato
        _athlete("FIC0004", "Loic Morel", "FRA", "tB"),         # ok → invariato
    ]
    await mock_db.athletes.insert_many(docs)
    before = {d["source_external_id"]: dict(d)
              for d in await mock_db.athletes.find({}).to_list(length=100)}

    changes = await rename_real_player_echoes(mock_db)
    assert {c["ext"] for c in changes} == {"FIC0197", "FIC0022"}

    after = {d["source_external_id"]: d for d in await mock_db.athletes.find({}).to_list(length=100)}

    # i 2 echi: nome cambiato, niente token vietato, nazionalità coerente, resto intatto
    for ext in ("FIC0197", "FIC0022"):
        old, new = before[ext], after[ext]
        assert new["internal_full_name"] != old["internal_full_name"]
        assert not (set(new["internal_full_name"].split()) & BANNED_REAL_PLAYER_TOKENS)
        first, last = new["internal_full_name"].split(" ", 1)
        assert first in NAME_POOLS[new["nationality_iso3"]]["first"]
        assert last in NAME_POOLS[new["nationality_iso3"]]["last"]
        assert new["display_label"].endswith(last[:8])
        # tutto il resto invariato
        for f in ("nationality_iso3", "role", "team_fantasy_id", "score_performance",
                  "prezzo_corrente_eur", "prezzo_iniziale_eur", "float_quote",
                  "primary_pool_qty", "valore_iniziale_eur", "source_external_id"):
            assert new[f] == old[f], f"{ext}: {f} cambiato!"

    # i 2 ok: completamente invariati
    for ext in ("FIC0003", "FIC0004"):
        assert after[ext]["internal_full_name"] == before[ext]["internal_full_name"]
        assert after[ext]["display_label"] == before[ext]["display_label"]


@pytest.mark.asyncio
async def test_cli_idempotent(mock_db):
    from app.cli.rename_real_player_echoes import rename_real_player_echoes

    await mock_db.athletes.insert_many([
        _athlete("FIC0197", "Lautaro Acosta", "ARG", "tA"),
        _athlete("FIC0022", "Domagoj Knezevic", "HRV", "tB"),
    ])
    first = await rename_real_player_echoes(mock_db)
    assert len(first) == 2
    second = await rename_real_player_echoes(mock_db)
    assert second == []  # nessun echo residuo
