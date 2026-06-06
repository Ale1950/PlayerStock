"""Engagement routes (Fase 6).

Endpoints (tutti JWT-protetti tranne dove indicato):
- POST   /api/engagement/streak/claim       → claim_daily_streak
- GET    /api/engagement/streak             → get_streak_state
- GET    /api/engagement/quizzes            → list_active_quizzes (pubblico-friendly ma JWT)
- POST   /api/engagement/quizzes/{id}/attempt  → submit_quiz_attempt
- POST   /api/engagement/predictions        → submit_prediction
- GET    /api/engagement/predictions        → get_my_predictions
- POST   /api/engagement/admin/settle-predictions  → settle_expired_predictions (admin)
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Query

from app.core.deps import AdminDep, CurrentUserDep, DBDep
from app.core.errors import err_bad_request
from app.modules.engagement.challenges import settle_weekly_challenge, weekly_challenge
from app.modules.engagement.missions import claim_mission, evaluate_missions
from app.modules.engagement.service import (
    claim_daily_streak, engagement_overview, get_my_predictions, get_streak_state,
    list_active_quizzes, settle_expired_predictions,
    submit_prediction, submit_quiz_attempt,
)

router = APIRouter(prefix="/engagement", tags=["engagement"])


@router.get("/overview")
async def get_overview(user: CurrentUserDep, db: DBDep):
    return await engagement_overview(db, user["_id"])


@router.get("/missions")
async def get_missions(user: CurrentUserDep, db: DBDep):
    return {"items": await evaluate_missions(db, user["_id"])}


@router.post("/missions/{mission_id}/claim")
async def post_claim_mission(mission_id: str, user: CurrentUserDep, db: DBDep):
    out = await claim_mission(db, user["_id"], mission_id)
    if not out.get("claimed") and (out.get("error") or out.get("incomplete")):
        raise err_bad_request("mission.not_claimable", "Missione non riscattabile", extra=out)
    return out


@router.get("/challenge")
async def get_challenge(user: CurrentUserDep, db: DBDep):
    return await weekly_challenge(db, user["_id"])


@router.post("/admin/settle-challenge")
async def post_settle_challenge(_: AdminDep, db: DBDep, week_key: Annotated[str, Body(embed=True)]):
    return await settle_weekly_challenge(db, week_key)


@router.post("/streak/claim")
async def post_streak_claim(user: CurrentUserDep, db: DBDep):
    return await claim_daily_streak(db, user["_id"])


@router.get("/streak")
async def get_streak(user: CurrentUserDep, db: DBDep):
    return await get_streak_state(db, user["_id"])


@router.get("/quizzes")
async def get_quizzes(_: CurrentUserDep, db: DBDep):
    items = await list_active_quizzes(db)
    return {"items": items, "count": len(items)}


@router.post("/quizzes/{quiz_id}/attempt")
async def post_quiz_attempt(quiz_id: str, user: CurrentUserDep, db: DBDep,
                            answers: list[int] = Body(..., embed=True)):
    out = await submit_quiz_attempt(db, user["_id"], quiz_id=quiz_id, answers=answers)
    if not out.get("ok"):
        raise err_bad_request(out.get("error_code", "quiz.error"),
                              out.get("error_code", "Errore quiz"), extra=out)
    return out


@router.post("/predictions")
async def post_prediction(user: CurrentUserDep, db: DBDep,
                          athlete_id: str = Body(..., embed=True),
                          direction: str = Body(..., embed=True)):
    out = await submit_prediction(db, user["_id"], athlete_id=athlete_id, direction=direction)
    if not out.get("ok"):
        raise err_bad_request(out.get("error_code", "prediction.error"),
                              out.get("error_code", "Errore previsione"), extra=out)
    return out


@router.get("/predictions")
async def list_my_predictions(user: CurrentUserDep, db: DBDep,
                              status: Annotated[str | None, Query()] = None,
                              limit: Annotated[int, Query(ge=1, le=100)] = 50):
    items = await get_my_predictions(db, user["_id"], status=status, limit=limit)
    return {"items": items, "count": len(items)}


@router.post("/admin/settle-predictions")
async def post_settle_predictions(_: AdminDep, db: DBDep,
                                  limit: Annotated[int, Query(ge=1, le=1000)] = 200):
    return await settle_expired_predictions(db, limit=limit)
