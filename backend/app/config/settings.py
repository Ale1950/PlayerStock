"""Application settings loaded from environment (.env)."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")


class Settings:
    # App
    APP_ENV: str = os.getenv("APP_ENV", "development")
    API_PREFIX: str = os.getenv("API_PREFIX", "/api")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    # Database
    MONGO_URL: str = os.environ["MONGO_URL"]
    DB_NAME: str = os.environ["DB_NAME"]

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-only-do-not-deploy")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRES_MIN: int = int(os.getenv("JWT_EXPIRES_MIN", "10080"))

    # Google OAuth
    GOOGLE_OAUTH_CLIENT_ID: str = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    GOOGLE_OAUTH_CLIENT_SECRET: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")

    # Roster provider: 'fictional_roster' (default, no token) | 'football_data_org'
    DATA_PROVIDER: str = os.getenv("DATA_PROVIDER", "fictional_roster")
    FOOTBALL_DATA_ORG_TOKEN: str = os.getenv("FOOTBALL_DATA_ORG_TOKEN", "")
    FOOTBALL_DATA_ORG_BASE_URL: str = os.getenv(
        "FOOTBALL_DATA_ORG_BASE_URL", "https://api.football-data.org/v4"
    )
    DATA_CACHE_TTL_FIXTURE_SEC: int = int(os.getenv("DATA_CACHE_TTL_FIXTURE_SEC", "3600"))
    DATA_CACHE_TTL_STATS_SEC: int = int(os.getenv("DATA_CACHE_TTL_STATS_SEC", "300"))

    # Admin
    ADMIN_BOOTSTRAP_EMAIL: str = os.getenv("ADMIN_BOOTSTRAP_EMAIL", "")

    # Game economy constants (mirrored from pricing_constants for quick access)
    BUDGET_INIZIALE_UTENTE: float = 10_000.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
