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

    # Reward NACKL (Fase 5). Internal = PLACEHOLDER dev; testnet = scaffold inerte (Q1/Q5).
    REWARD_PROVIDER: str = os.getenv("REWARD_PROVIDER", "internal")
    AN_NETWORK: str = os.getenv("AN_NETWORK", "shellnet")
    AN_APP_ID: str = os.getenv("AN_APP_ID", "")
    AN_GRAPHQL_ENDPOINT: str = os.getenv("AN_GRAPHQL_ENDPOINT", "")
    REWARD_HEARTBEAT_SECRET: str = os.getenv("REWARD_HEARTBEAT_SECRET", "dev-reward-secret")
    REWARD_HEARTBEAT_INTERVAL_SEC: int = int(os.getenv("REWARD_HEARTBEAT_INTERVAL_SEC", "300"))
    REWARD_DAILY_CAP_NACKL: float = float(os.getenv("REWARD_DAILY_CAP_NACKL", "50"))  # conservativo
    REWARD_BASE_PER_BEAT: float = float(os.getenv("REWARD_BASE_PER_BEAT", "0.1"))
    REWARD_PER_ACTIVITY: float = float(os.getenv("REWARD_PER_ACTIVITY", "1.0"))

    # Game economy constants (mirrored from pricing_constants for quick access)
    BUDGET_INIZIALE_UTENTE: float = 10_000.0

    # ── Deploy single-origin (D-deploy) ──
    # Cartella dell'export web Expo servita dal backend (/ → SPA). In Docker: /app/static.
    STATIC_DIR: str = os.getenv("STATIC_DIR", str(ROOT_DIR / "frontend" / "dist"))
    # Segreto per l'endpoint interno POST /api/internal/run-round (cron futuro).
    # VUOTO ⇒ endpoint DISABILITATO (503). Inerte senza segreto.
    INTERNAL_API_SECRET: str = os.getenv("INTERNAL_API_SECRET", "")

    # ── Prezzo guidato dalla performance (D10) — round forward che muovono il prezzo equo ──
    # Sorgente prestazioni a INNESTO: 'synthetic' (unica impl). Futuro: 'real' (post-legale).
    PERFORMANCE_FEED: str = os.getenv("PERFORMANCE_FEED", "synthetic")
    ROUND_ENABLED: bool = os.getenv("ROUND_ENABLED", "true").lower() in ("1", "true", "yes")
    # Default ATTIVO = VELOCE (mercato vivo in sviluppo). Realistico/prod: 10080 (settimanale).
    ROUND_INTERVAL_MIN: int = int(os.getenv("ROUND_INTERVAL_MIN", "30"))
    # Guadagno applicato alla performance% prima del clamp. Realistico: 1.0 (golden invariato).
    # Modalità veloce: ~2-3× per movimenti ben visibili. RANGE_CLAMP resta sempre rispettato.
    PERF_PRICE_GAIN: float = float(os.getenv("PERF_PRICE_GAIN", "2.5"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
