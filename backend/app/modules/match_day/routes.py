"""Match Day #2 — API stato evento (Fase 1, read-only)."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import DBDep
from app.market.match_day import get_current_match_day

router = APIRouter(prefix="/match-day", tags=["match-day"])


@router.get("/current")
async def current(db: DBDep):
    """Evento Match Day LIVE corrente + slate/prezzi + countdown. `{live: false}` se nessuno."""
    cur = await get_current_match_day(db)
    if cur is None:
        return {"live": False}
    cur["event_id"] = str(cur["event_id"])
    if cur.get("tournament_id") is not None:
        cur["tournament_id"] = str(cur["tournament_id"])
    return {"live": True, **cur}
