"""MongoDB connection (Motor async)."""
from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def init_db() -> None:
    """Initialize the global client. Call on app startup."""
    global _client, _db
    settings = get_settings()
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGO_URL)
        _db = _client[settings.DB_NAME]
        logger.info("MongoDB connected: db=%s", settings.DB_NAME)


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
