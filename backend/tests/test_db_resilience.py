"""TDD: resilienza startup — db_health non solleva mai (ok/degraded)."""
from __future__ import annotations

import asyncio

from app.core.db import db_health


class _OkDB:
    async def command(self, c):
        return {"ok": 1}


class _BadDB:
    async def command(self, c):
        raise RuntimeError("ServerSelectionTimeoutError: SSL handshake failed")


class _SlowDB:
    async def command(self, c):
        await asyncio.sleep(5)


async def test_db_health_ok():
    assert await db_health(_OkDB()) == "ok"


async def test_db_health_degraded_on_error():
    assert await db_health(_BadDB()) == "degraded"


async def test_db_health_degraded_on_timeout():
    assert await db_health(_SlowDB(), timeout=0.2) == "degraded"
