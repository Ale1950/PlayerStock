"""User-related Pydantic models."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.models.common import PyObjectId


class UserPublic(BaseModel):
    """User profile returned to the client (no internal fields)."""
    id: PyObjectId = Field(alias="_id")
    email: EmailStr
    name: str
    picture: str | None = None
    locale: str = "it"
    country_iso2: str | None = None
    role: Literal["user", "admin"] = "user"
    terms_accepted_at: datetime | None = None
    privacy_accepted_at: datetime | None = None
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = {"populate_by_name": True}


class WalletPublic(BaseModel):
    balance_eur: float
    updated_at: datetime


class UserWithWallet(BaseModel):
    user: UserPublic
    wallet: WalletPublic


class GoogleSignInRequest(BaseModel):
    id_token: str = Field(..., description="Google ID token (JWT) issued by Google Sign-In")
    locale: str | None = None


class GoogleCodeExchangeRequest(BaseModel):
    """Auth-code + PKCE: il client manda il code + verifier; il backend scambia con Google."""
    code: str = Field(..., description="Authorization code da Google")
    code_verifier: str = Field(..., description="PKCE code_verifier generato dal client")
    redirect_uri: str = Field(..., description="Stesso redirect_uri usato nella auth request")
    locale: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic
    wallet: WalletPublic


class AcceptTermsRequest(BaseModel):
    terms: bool
    privacy: bool


class UpdateLocaleRequest(BaseModel):
    locale: str
