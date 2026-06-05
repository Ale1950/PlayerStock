"""Pytest fixtures + test environment.

`app.config.settings` legge MONGO_URL/DB_NAME via os.environ[...] AL MOMENTO
dell'import (class body). Quindi questi env vars devono esistere PRIMA che
qualunque modulo `app.*` venga importato. conftest.py viene caricato da pytest
prima della collection dei test, perciò impostarli qui (top-level) è sufficiente.

I test NON si connettono ad Atlas: usano mongomock-motor (DB in-memory).
"""
from __future__ import annotations

import os

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "playerstock_test")
os.environ.setdefault("JWT_SECRET", "test-only-secret")

import pytest
from mongomock_motor import AsyncMongoMockClient


@pytest.fixture
def mock_db():
    """DB Motor in-memory (mongomock). Nessuna connessione di rete."""
    client = AsyncMongoMockClient()
    return client["playerstock_test"]
