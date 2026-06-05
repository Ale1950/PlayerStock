"""FastAPI dependencies (auth, db, current_user)."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config.settings import Settings, get_settings
from app.core.db import get_db
from app.core.errors import err_forbidden, err_unauthorized
from app.core.security import decode_token


async def current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Extract the user id from a Bearer JWT."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise err_unauthorized(code="auth.missing_token", msg="Token mancante")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except Exception:
        raise err_unauthorized(code="auth.invalid_token", msg="Token non valido o scaduto")
    sub = payload.get("sub")
    if not sub:
        raise err_unauthorized(code="auth.invalid_token", msg="Token non valido")
    return sub


async def current_user(
    user_id: Annotated[str, Depends(current_user_id)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> dict:
    from bson import ObjectId
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise err_unauthorized(code="auth.invalid_token", msg="Token non valido")
    user = await db.users.find_one({"_id": obj_id, "status": "active"})
    if not user:
        raise err_unauthorized(code="auth.user_not_found", msg="Utente non trovato")
    return user


async def require_admin(
    user: Annotated[dict, Depends(current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Bootstrap admin: l'email definita in ADMIN_BOOTSTRAP_EMAIL ha sempre accesso admin."""
    is_admin = user.get("role") == "admin" or (
        settings.ADMIN_BOOTSTRAP_EMAIL and user.get("email") == settings.ADMIN_BOOTSTRAP_EMAIL
    )
    if not is_admin:
        raise err_forbidden(code="auth.admin_required", msg="Permessi amministratore richiesti")
    return user


# Aliases for routes
SettingsDep = Annotated[Settings, Depends(get_settings)]
DBDep = Annotated[AsyncIOMotorDatabase, Depends(get_db)]
CurrentUserDep = Annotated[dict, Depends(current_user)]
AdminDep = Annotated[dict, Depends(require_admin)]
