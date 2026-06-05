"""Seed data for sports + fantasy teams. Idempotent."""
from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.teams_fantasy_map import SERIE_A_FANTASY_MAP
from app.models.common import utc_now

logger = logging.getLogger(__name__)


async def seed_sports(db: AsyncIOMotorDatabase) -> None:
    """Insert sports config. Idempotent."""
    sports = [
        {
            "_id": "calcio",
            "name_key": "sport.calcio.name",
            "roles": ["POR", "DIF", "CC", "ATT"],
            "active": True,
            "event_schema_version": "calcio_v1",
        },
        # Multi-sport ready (inactive in MVP)
        {"_id": "tennis", "name_key": "sport.tennis.name", "roles": ["SINGLE"], "active": False, "event_schema_version": "tennis_v1"},
        {"_id": "basket", "name_key": "sport.basket.name", "roles": ["PG", "SG", "SF", "PF", "C"], "active": False, "event_schema_version": "basket_v1"},
        {"_id": "f1",     "name_key": "sport.f1.name",     "roles": ["DRIVER"], "active": False, "event_schema_version": "f1_v1"},
    ]
    for s in sports:
        await db.sports.update_one({"_id": s["_id"]}, {"$setOnInsert": s}, upsert=True)
    logger.info("Sports seeded: %d", len(sports))


async def seed_teams_fantasy(db: AsyncIOMotorDatabase) -> None:
    """Insert Serie A fantasy teams. Idempotent."""
    now = utc_now()
    for team in SERIE_A_FANTASY_MAP:
        doc = {
            "sport_id": "calcio",
            "internal_real_id": team["real_id_internal"],
            "internal_real_name": team["real_name_internal"],
            "fantasy_name": team["fantasy_name"],
            "city": team["city"],
            "color_primary": team["color_primary"],
            "color_secondary": team["color_secondary"],
            "country_iso3": team["country_iso3"],
            "fd_org_match_names": team["fd_org_match_names"],
            "updated_at": now,
        }
        await db.teams_fantasy.update_one(
            {"sport_id": "calcio", "internal_real_id": team["real_id_internal"]},
            {"$set": doc, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
    logger.info("Serie A fantasy teams seeded: %d", len(SERIE_A_FANTASY_MAP))


async def run_all_seeds(db: AsyncIOMotorDatabase) -> None:
    await seed_sports(db)
    await seed_teams_fantasy(db)
