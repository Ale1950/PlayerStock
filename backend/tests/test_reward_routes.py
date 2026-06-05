"""RED→GREEN: endpoint /api/reward (balance, provider, wallet connect, heartbeat)."""
from __future__ import annotations

import asyncio
import hashlib
import hmac

from bson import ObjectId
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

from app.config.settings import get_settings
from app.core.db import get_db
from app.core.deps import current_user
from app.main import app


class _Settings:
    REWARD_PROVIDER = "internal"
    AN_NETWORK = "shellnet"
    AN_APP_ID = ""
    AN_GRAPHQL_ENDPOINT = ""
    REWARD_HEARTBEAT_SECRET = "test-secret"
    REWARD_HEARTBEAT_INTERVAL_SEC = 300
    REWARD_DAILY_CAP_NACKL = 50.0
    REWARD_BASE_PER_BEAT = 0.1
    REWARD_PER_ACTIVITY = 1.0


def _client():
    db = AsyncMongoMockClient()["playerstock_test"]
    uid = ObjectId()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[current_user] = lambda: {"_id": uid, "status": "active", "role": "user"}
    app.dependency_overrides[get_settings] = lambda: _Settings()
    return TestClient(app), uid


def teardown_function():
    app.dependency_overrides.clear()


def test_provider_info_is_placeholder():
    client, _ = _client()
    r = client.get("/api/reward/provider")
    assert r.status_code == 200
    b = r.json()
    assert b["is_placeholder"] is True
    assert b["wallet_connected"] is False
    assert b["mining_status"] == "coming_soon"


def test_balance_starts_zero_placeholder():
    client, _ = _client()
    b = client.get("/api/reward/balance").json()
    assert b["amount"] == 0.0
    assert b["is_placeholder"] is True
    assert b["currency"] == "NACKL"


def test_wallet_connect_accepts_public_key():
    client, _ = _client()
    r = client.post("/api/reward/wallet/connect", json={"mining_public_key": "0x" + "a" * 64})
    assert r.status_code == 200
    assert r.json()["connected"] is True
    assert client.get("/api/reward/provider").json()["wallet_connected"] is True


def test_wallet_connect_rejects_seed():
    client, _ = _client()
    seed = "legal winner thank year wave sausage worth useful legal winner thank yellow"
    r = client.post("/api/reward/wallet/connect", json={"mining_public_key": seed})
    assert r.status_code == 400
    assert r.json()["detail"]["error_code"] == "reward.wallet.seed_not_allowed"


def test_heartbeat_accrues():
    client, uid = _client()
    nonce, ts = "n1", 1000
    msg = f"{uid}:{nonce}:{ts}"
    sig = hmac.new(b"test-secret", msg.encode(), hashlib.sha256).hexdigest()
    r = client.post("/api/reward/heartbeat", json={"nonce": nonce, "ts": ts, "signature": sig})
    assert r.status_code == 200, r.text
    assert r.json()["accrued"] >= 0.1  # almeno la base passiva


def test_heartbeat_bad_signature_401():
    client, _ = _client()
    r = client.post("/api/reward/heartbeat", json={"nonce": "x", "ts": 1, "signature": "bad"})
    assert r.status_code == 401
