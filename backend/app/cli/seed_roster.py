"""CLI: popola DB con sports/teams + roster 400 giocatori Serie A.

Uso (dalla cartella backend/):
    python -m app.cli.seed_roster --season 2024 --limit 20
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from app.config.settings import get_settings
from app.config.teams_fantasy_map import find_fantasy_by_real_name
from app.core.db import close_db, get_db, init_db
from app.data_providers.anonymization import anonymize_name
from app.data_providers.football_data_org import FootballDataOrgProvider
from app.db.indexes import ensure_indexes
from app.db.seed import run_all_seeds
from app.models.common import utc_now
from app.config.pricing_constants import (
    FLOAT_AZIONI_PER_GIOCATORE,
    PREZZO_BASE_AZIONE_CREDITI,
    VALORE_BASE_GIOCATORE_CREDITI,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_cli")


async def main(season: int, limit_per_team: int) -> int:
    settings = get_settings()
    if not settings.FOOTBALL_DATA_ORG_TOKEN:
        logger.error("FOOTBALL_DATA_ORG_TOKEN non configurato in .env")
        return 1

    init_db()
    db = get_db()
    await ensure_indexes(db)
    await run_all_seeds(db)

    provider = FootballDataOrgProvider(
        api_token=settings.FOOTBALL_DATA_ORG_TOKEN,
        base_url=settings.FOOTBALL_DATA_ORG_BASE_URL,
    )

    logger.info("Fetching Serie A roster season=%d ...", season)
    players = await provider.fetch_serie_a_full(season=season)
    logger.info("Totale giocatori scaricati: %d", len(players))

    team_docs = await db.teams_fantasy.find({"sport_id": "calcio"}).to_list(length=100)
    team_by_alias: dict[str, dict] = {}
    for t in team_docs:
        for alias in t.get("fd_org_match_names", []):
            team_by_alias[alias.lower()] = t
        team_by_alias[t["internal_real_name"].lower()] = t

    by_team: dict[str, list[dict]] = {}
    for p in players:
        fd_name = (p.get("team_fd_name") or "").strip()
        if fd_name:
            by_team.setdefault(fd_name, []).append(p)

    now = utc_now()
    items_synced = 0
    skipped_no_team = 0
    skipped_dup = 0
    errors: list[str] = []

    for fd_team_name, team_players in by_team.items():
        team_doc = team_by_alias.get(fd_team_name.lower())
        if not team_doc:
            fb = find_fantasy_by_real_name(fd_team_name)
            if fb:
                team_doc = await db.teams_fantasy.find_one({
                    "sport_id": "calcio",
                    "internal_real_id": fb["real_id_internal"],
                })
        if not team_doc:
            skipped_no_team += len(team_players)
            logger.warning("Squadra non mappata: %s (%d giocatori)", fd_team_name, len(team_players))
            continue

        by_role: dict[str, list[dict]] = {"POR": [], "DIF": [], "CC": [], "ATT": []}
        for p in team_players:
            by_role.setdefault(p["role"], []).append(p)
        target = {"POR": 2, "DIF": 6, "CC": 6, "ATT": 6}
        if limit_per_team != 20:
            scale = limit_per_team / 20.0
            target = {k: max(1, round(v * scale)) for k, v in target.items()}
        selected: list[dict] = []
        for r, n in target.items():
            selected.extend(by_role.get(r, [])[:n])
        already = {p["external_id"] for p in selected}
        for p in team_players:
            if len(selected) >= limit_per_team:
                break
            if p["external_id"] not in already:
                selected.append(p)

        for p in selected[:limit_per_team]:
            name = p["internal_full_name"]
            initial, lastname, label = anonymize_name(name)
            doc = {
                "sport_id": "calcio",
                "internal_full_name": name,
                "display_initial": initial,
                "display_lastname": lastname,
                "display_label": label,
                "nationality_iso3": p["nationality_iso3"],
                "role": p["role"],
                "age": p.get("age"),
                "team_fantasy_id": team_doc["_id"],
                "minutaggio_pct": 0.75,
                "valore_iniziale_crediti": VALORE_BASE_GIOCATORE_CREDITI,
                "float_quote": FLOAT_AZIONI_PER_GIOCATORE,
                "prezzo_iniziale_crediti": PREZZO_BASE_AZIONE_CREDITI,
                "prezzo_corrente_crediti": PREZZO_BASE_AZIONE_CREDITI,
                "status": "ACTIVE",
                "data_source": "football_data_org",
                "source_external_id": p["external_id"],
                "updated_at": now,
            }
            try:
                res = await db.athletes.update_one(
                    {"sport_id": "calcio", "internal_full_name": name, "team_fantasy_id": team_doc["_id"]},
                    {"$set": doc, "$setOnInsert": {"created_at": now}},
                    upsert=True,
                )
                if res.upserted_id or res.modified_count:
                    items_synced += 1
                else:
                    skipped_dup += 1
            except Exception as e:
                errors.append(f"{name}@{fd_team_name}: {e}")

    await db.data_sync_log.insert_one({
        "source": provider.provider_name,
        "endpoint": f"/competitions/SA/teams?season={season}",
        "status": "ok" if not errors else "partial",
        "items_synced": items_synced,
        "skipped_no_team": skipped_no_team,
        "skipped_dup": skipped_dup,
        "errors_count": len(errors),
        "errors_sample": errors[:5],
        "ran_at": now,
        "finished_at": utc_now(),
    })

    logger.info("✅ DONE | synced=%d | skipped_no_team=%d | dup=%d | errors=%d",
                items_synced, skipped_no_team, skipped_dup, len(errors))
    if errors:
        for e in errors[:5]:
            logger.warning("  → %s", e)

    close_db()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2024)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.season, args.limit)))
