"""Endpoint aggregati (backbone dati): market-wide, per-giocatore, per-utente."""
from __future__ import annotations

from bson import ObjectId
from fastapi import APIRouter, Query

from app.core.deps import CurrentUserDep, DBDep
from app.core.errors import err_not_found
from app.modules.stats.analytics import leaderboard_analytics, user_analytics
from app.modules.stats.service import (
    athlete_market_stats,
    market_overview,
    user_market_stats,
)

router = APIRouter(tags=["stats"])


@router.get("/stats/me/analytics")
async def stats_me_analytics(
    user: CurrentUserDep, db: DBDep, period: str = Query("1M", pattern="^(1S|1M|3M|all)$"),
) -> dict:
    return await user_analytics(db, user["_id"], period=period)


@router.get("/stats/leaderboard-analytics")
async def stats_leaderboard_analytics(
    user: CurrentUserDep, db: DBDep,
    period: str = Query("1M", pattern="^(1S|1M|3M|all)$"),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    return await leaderboard_analytics(db, user["_id"], period=period, limit=limit)


@router.get("/stats/market")
async def stats_market(db: DBDep) -> dict:
    return await market_overview(db)


@router.get("/stats/athletes/{athlete_id}")
async def stats_athlete(athlete_id: str, db: DBDep) -> dict:
    try:
        aid = ObjectId(athlete_id)
    except Exception:
        raise err_not_found("athlete.invalid_id", "ID atleta non valido")
    st = await athlete_market_stats(db, aid)
    if not st:
        raise err_not_found("athlete.not_found", "Atleta non trovato")
    return st


@router.get("/stats/me")
async def stats_me(user: CurrentUserDep, db: DBDep) -> dict:
    return await user_market_stats(db, user["_id"])
