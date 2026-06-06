"""Auth module: Google OAuth + JWT issuance."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.config.pricing_constants import BUDGET_INIZIALE_UTENTE_EUR
from app.config.settings import get_settings
from app.core.deps import CurrentUserDep, DBDep, SettingsDep
from app.core.errors import err_bad_request, err_unauthorized
from app.core.security import create_access_token
from app.models.common import utc_now
from app.models.user import (
    AcceptTermsRequest,
    AuthResponse,
    GoogleCodeExchangeRequest,
    GoogleSignInRequest,
    UpdateLocaleRequest,
    UserPublic,
    WalletPublic,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _verify_google_id_token(token: str, client_id: str) -> dict:
    try:
        info = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), client_id, clock_skew_in_seconds=10
        )
        # Audience checks
        if info.get("aud") != client_id:
            raise ValueError("Audience mismatch")
        if not info.get("email_verified"):
            raise ValueError("Email not verified")
        return info
    except Exception as e:
        logger.warning("Google id_token verification failed: %s", e)
        raise err_unauthorized(code="auth.google_invalid_token", msg="Token Google non valido")


async def _exchange_code_for_id_token(*, code: str, code_verifier: str, redirect_uri: str, settings) -> str:
    """Auth-code + PKCE: scambia il code con Google e ritorna l'id_token."""
    import httpx

    data = {
        "code": code,
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post("https://oauth2.googleapis.com/token", data=data)
    except Exception as e:  # noqa: BLE001
        logger.warning("Google token exchange network error: %s", e)
        raise err_unauthorized(code="auth.google_exchange_failed", msg="Scambio token Google fallito")
    if resp.status_code != 200:
        logger.warning("Google token exchange failed %s: %s", resp.status_code, resp.text[:300])
        raise err_unauthorized(code="auth.google_exchange_failed", msg="Scambio token Google fallito")
    id_tok = resp.json().get("id_token")
    if not id_tok:
        raise err_unauthorized(code="auth.google_exchange_failed", msg="id_token assente nella risposta Google")
    return id_tok


async def _provision_user_and_issue(db, settings, info: dict, req_locale: str | None) -> AuthResponse:
    """Crea/aggiorna utente + wallet dall'id_token verificato ed emette il JWT app."""
    google_sub = info["sub"]
    email = info.get("email")
    name = info.get("name") or (email.split("@")[0] if email else "User")
    picture = info.get("picture")
    locale = (req_locale or info.get("locale") or "it").lower()[:2]

    now = utc_now()
    existing = await db.users.find_one({"google_sub": google_sub})

    if existing:
        await db.users.update_one(
            {"_id": existing["_id"]},
            {"$set": {"last_login_at": now, "name": name, "picture": picture, "locale": locale}},
        )
        user_id = existing["_id"]
        wallet = await db.user_wallets.find_one({"user_id": user_id})
        if not wallet:
            # Defensive: bootstrap wallet if missing
            wallet = {"user_id": user_id, "balance_eur": BUDGET_INIZIALE_UTENTE_EUR, "updated_at": now}
            await db.user_wallets.insert_one(wallet)
            await db.wallet_transactions.insert_one({
                "user_id": user_id, "type": "welcome_bonus",
                "amount": BUDGET_INIZIALE_UTENTE_EUR, "balance_after": BUDGET_INIZIALE_UTENTE_EUR,
                "description_it": "Bonus di benvenuto",
                "created_at": now,
            })
    else:
        # Determine role (admin if bootstrap email matches)
        role = "admin" if (settings.ADMIN_BOOTSTRAP_EMAIL and email == settings.ADMIN_BOOTSTRAP_EMAIL) else "user"
        user_doc = {
            "google_sub": google_sub, "email": email, "name": name, "picture": picture,
            "locale": locale, "country_iso2": None, "role": role,
            "terms_accepted_at": None, "privacy_accepted_at": None,
            "created_at": now, "last_login_at": now,
            "status": "active", "delete_requested_at": None,
        }
        result = await db.users.insert_one(user_doc)
        user_id = result.inserted_id
        # Bootstrap wallet with welcome bonus
        wallet_doc = {"user_id": user_id, "balance_eur": BUDGET_INIZIALE_UTENTE_EUR, "updated_at": now}
        await db.user_wallets.insert_one(wallet_doc)
        await db.wallet_transactions.insert_one({
            "user_id": user_id, "type": "welcome_bonus",
            "amount": BUDGET_INIZIALE_UTENTE_EUR, "balance_after": BUDGET_INIZIALE_UTENTE_EUR,
            "description_it": "Bonus di benvenuto",
            "created_at": now,
        })

    # Reload user
    user = await db.users.find_one({"_id": user_id})
    wallet = await db.user_wallets.find_one({"user_id": user_id})

    access_token = create_access_token(user_id=str(user_id))

    return AuthResponse(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRES_MIN * 60,
        user=UserPublic.model_validate(user),
        wallet=WalletPublic(balance_eur=wallet["balance_eur"], updated_at=wallet["updated_at"]),
    )


@router.post("/google/callback", response_model=AuthResponse)
async def google_callback(req: GoogleSignInRequest, db: DBDep, settings: SettingsDep) -> AuthResponse:
    """Flusso id_token diretto (mobile nativo / GSI). Verifica l'id_token ed emette il JWT."""
    if not settings.GOOGLE_OAUTH_CLIENT_ID:
        raise err_bad_request("auth.google_not_configured", "Google OAuth non configurato sul server")
    info = _verify_google_id_token(req.id_token, settings.GOOGLE_OAUTH_CLIENT_ID)
    return await _provision_user_and_issue(db, settings, info, req.locale)


@router.post("/google/exchange", response_model=AuthResponse)
async def google_exchange(req: GoogleCodeExchangeRequest, db: DBDep, settings: SettingsDep) -> AuthResponse:
    """Flusso auth-code + PKCE (web/mobile): scambia il code lato backend, verifica, emette il JWT."""
    if not (settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET):
        raise err_bad_request("auth.google_not_configured", "Google OAuth non configurato sul server")
    id_tok = await _exchange_code_for_id_token(
        code=req.code, code_verifier=req.code_verifier,
        redirect_uri=req.redirect_uri, settings=settings,
    )
    info = _verify_google_id_token(id_tok, settings.GOOGLE_OAUTH_CLIENT_ID)
    return await _provision_user_and_issue(db, settings, info, req.locale)


@router.post("/refresh")
async def refresh(user: CurrentUserDep):
    """Issue a fresh JWT for the current user."""
    settings = get_settings()
    access_token = create_access_token(user_id=str(user["_id"]))
    return {"access_token": access_token, "token_type": "bearer", "expires_in": settings.JWT_EXPIRES_MIN * 60}


@router.post("/logout")
async def logout(user: CurrentUserDep):
    """In MVP stateless JWT, logout is client-side (drop the token)."""
    return {"ok": True}


@router.delete("/me")
async def delete_account(user: CurrentUserDep, db: DBDep):
    """GDPR soft-delete: marca utente come 'deleted' e svuota dati."""
    now = utc_now()
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"status": "deleted", "delete_requested_at": now, "email": f"deleted_{user['_id']}@playerstock.app"}},
    )
    return {"ok": True, "deleted_at": now.isoformat()}
