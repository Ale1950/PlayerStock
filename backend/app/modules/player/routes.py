"""Player module: roster Serie A (Livello 2 anonimizzazione)."""
from __future__ import annotations

from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Query

from app.core.deps import DBDep
from app.core.errors import err_not_found
from app.models.athlete import (
    AthleteListResponse,
    AthletePublic,
    SportPublic,
    TeamFantasyPublic,
)

router = APIRouter(tags=["players"])


def _athlete_doc_to_public(doc: dict) -> AthletePublic:
    return AthletePublic.model_validate(doc)


@router.get("/sports", response_model=list[SportPublic])
async def list_sports(db: DBDep):
    cursor = db.sports.find({})
    items = await cursor.to_list(length=20)
    return [SportPublic.model_validate(s) for s in items]


@router.get("/teams", response_model=list[TeamFantasyPublic])
async def list_teams(db: DBDep, sport_id: str = Query("calcio")):
    cursor = db.teams_fantasy.find({"sport_id": sport_id}).sort("fantasy_name", 1)
    items = await cursor.to_list(length=100)
    # Strip internal fields before returning
    safe_items = []
    for t in items:
        safe_items.append({
            "_id": t["_id"], "sport_id": t["sport_id"], "fantasy_name": t["fantasy_name"],
            "city": t["city"], "color_primary": t["color_primary"],
            "color_secondary": t["color_secondary"], "country_iso3": t["country_iso3"],
        })
    return [TeamFantasyPublic.model_validate(t) for t in safe_items]


@router.get("/players", response_model=AthleteListResponse)
async def list_players(
    db: DBDep,
    sport_id: str = Query("calcio"),
    role: str | None = Query(None, description="POR|DIF|CC|ATT"),
    team_id: str | None = Query(None),
    q: str | None = Query(None, description="Search by display_label"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    filt: dict = {"sport_id": sport_id, "status": "ACTIVE"}
    if role:
        filt["role"] = role.upper()
    if team_id:
        try:
            filt["team_fantasy_id"] = ObjectId(team_id)
        except Exception:
            raise err_not_found("team.invalid_id", "team_id non valido")
    if q:
        filt["display_label"] = {"$regex": q, "$options": "i"}

    total = await db.athletes.count_documents(filt)
    skip = (page - 1) * page_size

    # Aggregate to denormalize team fantasy fields for fast UI
    pipeline = [
        {"$match": filt},
        {"$sort": {"prezzo_corrente_crediti": -1, "display_label": 1}},
        {"$skip": skip},
        {"$limit": page_size},
        {"$lookup": {
            "from": "teams_fantasy",
            "localField": "team_fantasy_id",
            "foreignField": "_id",
            "as": "team",
        }},
        {"$unwind": {"path": "$team", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "internal_full_name": 0,  # NEVER expose
            "team.internal_real_id": 0,
            "team.internal_real_name": 0,
            "team.fd_org_match_names": 0,
        }},
    ]
    raw_items = await db.athletes.aggregate(pipeline).to_list(length=page_size)
    items: list[AthletePublic] = []
    for doc in raw_items:
        team = doc.pop("team", None) or {}
        doc["team_fantasy_name"] = team.get("fantasy_name")
        doc["team_color_primary"] = team.get("color_primary")
        items.append(AthletePublic.model_validate(doc))
    return AthleteListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/players/{player_id}", response_model=AthletePublic)
async def get_player(player_id: str, db: DBDep):
    try:
        oid = ObjectId(player_id)
    except Exception:
        raise err_not_found("player.invalid_id", "ID giocatore non valido")
    pipeline = [
        {"$match": {"_id": oid}},
        {"$lookup": {"from": "teams_fantasy", "localField": "team_fantasy_id", "foreignField": "_id", "as": "team"}},
        {"$unwind": {"path": "$team", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "internal_full_name": 0,
            "team.internal_real_id": 0,
            "team.internal_real_name": 0,
            "team.fd_org_match_names": 0,
        }},
    ]
    docs = await db.athletes.aggregate(pipeline).to_list(length=1)
    if not docs:
        raise err_not_found("player.not_found", "Giocatore non trovato")
    doc = docs[0]
    team = doc.pop("team", None) or {}
    doc["team_fantasy_name"] = team.get("fantasy_name")
    doc["team_color_primary"] = team.get("color_primary")
    return AthletePublic.model_validate(doc)
