"""Admin module: protected endpoints for seeding & ops."""
from __future__ import annotations

import asyncio
import logging
import random
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query

from app.config.pricing_constants import (
    FLOAT_AZIONI_PER_GIOCATORE,
    PREZZO_BASE_AZIONE_EUR,
    VALORE_BASE_GIOCATORE_EUR,
)
from app.config.settings import get_settings
from app.config.teams_fantasy_map import find_fantasy_by_real_name
from app.core.deps import AdminDep, DBDep
from app.core.errors import err_bad_request
from app.data_providers.anonymization import anonymize_name
from app.data_providers.football_data_org import FootballDataOrgProvider
from app.db.seed import run_all_seeds
from app.models.common import utc_now

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed/sports-teams")
async def seed_sports_teams(_: AdminDep, db: DBDep):
    """Idempotente: popola sports + teams_fantasy Serie A."""
    await run_all_seeds(db)
    return {"ok": True, "msg": "Sports e squadre fantasy seedati"}


@router.post("/seed/serie-a-roster")
async def seed_serie_a_roster(
    _: AdminDep,
    db: DBDep,
    season: Annotated[int, Query(ge=2020, le=2030)] = 2024,
    limit_per_team: Annotated[int, Query(ge=1, le=40)] = 20,
):
    """Scarica il roster Serie A da Football-Data.org e popola la collezione athletes.

    Mappatura squadre via teams_fantasy_map (Livello 2).
    Idempotente: usa upsert su (sport_id, internal_full_name, team_fantasy_id).
    """
    settings = get_settings()
    if not settings.FOOTBALL_DATA_ORG_TOKEN:
        raise err_bad_request("data.no_token", "Football-Data.org token non configurato")

    provider = FootballDataOrgProvider(
        api_token=settings.FOOTBALL_DATA_ORG_TOKEN,
        base_url=settings.FOOTBALL_DATA_ORG_BASE_URL,
    )

    sync_started_at = utc_now()
    items_synced = 0
    skipped_no_team = 0
    skipped_dup = 0
    errors: list[str] = []

    try:
        players = await provider.fetch_serie_a_full(season=season)
    except Exception as e:
        await db.data_sync_log.insert_one({
            "source": provider.provider_name,
            "endpoint": f"/competitions/SA/teams?season={season}",
            "status": "error",
            "items_synced": 0,
            "error_msg": str(e),
            "ran_at": sync_started_at,
        })
        raise err_bad_request("data.fetch_failed", f"Errore fetch Football-Data.org: {e}")

    # Build team_fd_id -> team_fantasy_doc map
    team_docs = await db.teams_fantasy.find({"sport_id": "calcio"}).to_list(length=100)
    team_by_real_name: dict[str, dict] = {t["internal_real_name"].lower(): t for t in team_docs}
    team_by_fd_alias: dict[str, dict] = {}
    for t in team_docs:
        for alias in t.get("fd_org_match_names", []):
            team_by_fd_alias[alias.lower()] = t

    # Group players by team and cap to limit_per_team
    by_team: dict[str, list[dict]] = {}
    for p in players:
        fd_name = (p.get("team_fd_name") or "").strip()
        if not fd_name:
            continue
        by_team.setdefault(fd_name, []).append(p)

    now = utc_now()
    for fd_team_name, team_players in by_team.items():
        # Find fantasy team
        team_doc = team_by_fd_alias.get(fd_team_name.lower()) or team_by_real_name.get(fd_team_name.lower())
        if not team_doc:
            fallback = find_fantasy_by_real_name(fd_team_name)
            if fallback:
                team_doc = await db.teams_fantasy.find_one({
                    "sport_id": "calcio",
                    "internal_real_id": fallback["real_id_internal"],
                })
        if not team_doc:
            skipped_no_team += len(team_players)
            errors.append(f"Squadra fantasy non trovata: {fd_team_name}")
            continue

        # Diversifica ruoli: prendi al massimo limit_per_team con bilanciamento
        # (FD.org gratuito già limita a ~20-30; in caso, ordina mantenendo varietà di ruoli)
        random.seed(hash(fd_team_name) & 0xFFFFFFFF)
        # ordina per ruolo preservando proporzioni: POR 2, DIF 6, CC 6, ATT 6
        by_role: dict[str, list[dict]] = {"POR": [], "DIF": [], "CC": [], "ATT": []}
        for p in team_players:
            r = p["role"]
            by_role.setdefault(r, []).append(p)
        target = {"POR": 2, "DIF": 6, "CC": 6, "ATT": 6}
        # adatta se la squadra è limit_per_team≠20
        if limit_per_team != 20:
            scale = limit_per_team / 20.0
            target = {k: max(1, round(v * scale)) for k, v in target.items()}
        selected: list[dict] = []
        for r, n in target.items():
            selected.extend(by_role.get(r, [])[:n])
        # Riempi gli slot rimanenti con quelli non selezionati
        already_ids = {p["external_id"] for p in selected}
        for p in team_players:
            if len(selected) >= limit_per_team:
                break
            if p["external_id"] not in already_ids:
                selected.append(p)

        for p in selected[:limit_per_team]:
            internal_name = p["internal_full_name"]
            initial, lastname, label = anonymize_name(internal_name)
            doc = {
                "sport_id": "calcio",
                "internal_full_name": internal_name,  # DB only
                "display_initial": initial,
                "display_lastname": lastname,
                "display_label": label,
                "nationality_iso3": p["nationality_iso3"],
                "role": p["role"],
                "age": p.get("age"),
                "team_fantasy_id": team_doc["_id"],
                "minutaggio_pct": 0.75,  # placeholder; Fase 2 leggerà stats reali
                # Pricing placeholder (Fase 2 ricalcola)
                "valore_iniziale_eur": VALORE_BASE_GIOCATORE_EUR,
                "float_quote": FLOAT_AZIONI_PER_GIOCATORE,
                "prezzo_iniziale_eur": PREZZO_BASE_AZIONE_EUR,
                "prezzo_corrente_eur": PREZZO_BASE_AZIONE_EUR,
                "status": "ACTIVE",
                "data_source": "football_data_org",
                "source_external_id": p["external_id"],
                "updated_at": now,
            }
            try:
                result = await db.athletes.update_one(
                    {
                        "sport_id": "calcio",
                        "internal_full_name": internal_name,
                        "team_fantasy_id": team_doc["_id"],
                    },
                    {"$set": doc, "$setOnInsert": {"created_at": now}},
                    upsert=True,
                )
                if result.upserted_id or result.modified_count:
                    items_synced += 1
                else:
                    skipped_dup += 1
            except Exception as e:
                errors.append(f"{internal_name}@{fd_team_name}: {e}")

    await db.data_sync_log.insert_one({
        "source": provider.provider_name,
        "endpoint": f"/competitions/SA/teams?season={season}",
        "status": "ok" if not errors else "partial",
        "items_synced": items_synced,
        "skipped_no_team": skipped_no_team,
        "skipped_dup": skipped_dup,
        "errors_count": len(errors),
        "errors_sample": errors[:5],
        "ran_at": sync_started_at,
        "finished_at": utc_now(),
    })

    return {
        "ok": True,
        "items_synced": items_synced,
        "skipped_no_team": skipped_no_team,
        "skipped_dup": skipped_dup,
        "errors": len(errors),
        "errors_sample": errors[:5],
    }


@router.get("/data-sync-log")
async def get_sync_log(_: AdminDep, db: DBDep, limit: int = 20):
    cursor = db.data_sync_log.find({}, {"_id": 0}).sort("ran_at", -1).limit(limit)
    items = await cursor.to_list(length=limit)
    # serialize datetime
    for it in items:
        for k in ["ran_at", "finished_at"]:
            if k in it and it[k] is not None:
                it[k] = it[k].isoformat()
    return {"items": items}


@router.get("/stats")
async def admin_stats(_: AdminDep, db: DBDep):
    """Counts per collection (admin dashboard)."""
    stats = {
        "users": await db.users.count_documents({"status": "active"}),
        "users_deleted": await db.users.count_documents({"status": "deleted"}),
        "athletes": await db.athletes.count_documents({"status": "ACTIVE"}),
        "teams_fantasy": await db.teams_fantasy.count_documents({}),
        "sports": await db.sports.count_documents({}),
        "wallet_transactions": await db.wallet_transactions.count_documents({}),
    }
    # athletes per role
    pipeline = [{"$match": {"status": "ACTIVE"}}, {"$group": {"_id": "$role", "n": {"$sum": 1}}}]
    by_role = await db.athletes.aggregate(pipeline).to_list(length=10)
    stats["athletes_by_role"] = {r["_id"]: r["n"] for r in by_role}
    return stats
