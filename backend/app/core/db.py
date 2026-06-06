"""MongoDB connection (Motor async).

Motor è LAZY: `init_db()` crea il client ma NON apre la connessione (avviene alla
prima operazione, con riconnessione automatica). Quindi l'app può partire anche con
Atlas momentaneamente giù; le operazioni falliscono finché Atlas non torna, poi
motor si riconnette da solo. `serverSelectionTimeoutMS` basso = fallimento RAPIDO
(non 30s) durante i blip.
"""
from __future__ import annotations

import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def init_db() -> None:
    """Initialize the global client (lazy: nessuna connessione qui)."""
    global _client, _db
    settings = get_settings()
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.MONGO_URL,
            serverSelectionTimeoutMS=8000,   # blip Atlas → fallisce in 8s, non 30s
            connectTimeoutMS=8000,
            retryWrites=True,
        )
        _db = _client[settings.DB_NAME]
        logger.info("MongoDB client init: db=%s (connessione lazy)", settings.DB_NAME)


async def db_health(db: AsyncIOMotorDatabase | None = None, *, timeout: float = 3.0) -> str:
    """Stato DB per /health: 'ok' se il ping risponde, 'degraded' altrimenti (mai solleva)."""
    target = db if db is not None else get_db()
    try:
        await asyncio.wait_for(target.command("ping"), timeout=timeout)
        return "ok"
    except Exception:
        return "degraded"


def close_db() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        init_db()
    assert _db is not None
    return _db
