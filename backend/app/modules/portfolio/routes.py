"""Portfolio routes (Fase 4): /api/portfolio, /api/wallet, /api/leaderboard,
/api/athletes/{id}/price-history."""
from __future__ import annotations

from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Query

from app.core.deps import CurrentUserDep, DBDep
from app.core.errors import err_not_found
from app.modules.portfolio.service import (
    build_leaderboard,
    build_portfolio_response,
    build_wallet_response,
    fetch_price_history,
)

router = APIRouter(tags=["portfolio"])


def _oid(value: str, code: str, msg: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception:
        raise err_not_found(code, msg)


@router.get("/portfolio")
async def get_portfolio(user: CurrentUserDep, db: DBDep) -> dict:
    """Posizioni dell'utente + totali (cassa, valore titoli, P&L assoluto e %).

    Anonimizzazione Livello 2 sempre: nessun nome reale, nessun internal_*.
    """
    return await build_portfolio_response(db, user["_id"])


@router.get("/wallet")
async def get_wallet_unified(
    user: CurrentUserDep, db: DBDep,
    recent: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    """Endpoint UNIFICATO: saldo crediti + ultime N transazioni.

    Per compatibilità retroattiva restano disponibili anche
    GET /api/wallet/balance e GET /api/wallet/transactions (Fase 1).
    """
    return await build_wallet_response(db, user["_id"], recent_limit=recent)


@router.get("/leaderboard")
async def get_leaderboard(
    user: CurrentUserDep, db: DBDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict:
    """Top utenti per equity totale (cassa + valore titoli).

    Privacy: nome troncato "Mario R." per chi non è l'utente corrente.
    Nessun email/user_id esposto.
    """
    return await build_leaderboard(db, user["_id"], limit=limit)


@router.get("/athletes/{athlete_id}/price-history")
async def get_price_history(
    athlete_id: str, db: DBDep,
    limit: Annotated[int, Query(ge=2, le=200)] = 30,
) -> dict:
    """Punti recenti per sparkline. Pubblico (no auth) — sono dati di mercato."""
    aid = _oid(athlete_id, "athlete.invalid_id", "ID atleta non valido")
    points = await fetch_price_history(db, aid, limit=limit)
    return {"athlete_id": athlete_id, "points": points, "count": len(points)}
