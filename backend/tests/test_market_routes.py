"""RED→GREEN: endpoint /api/market (buy/sell, holdings, quote)."""
from __future__ import annotations

import asyncio

from bson import ObjectId
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

from app.core.db import get_db
from app.core.deps import current_user
from app.main import app
from app.models.common import utc_now


def _make_client(balance=100.0, price=0.02, pool=1_000_000):
    db = AsyncMongoMockClient()["playerstock_test"]
    uid = ObjectId()

    async def _seed():
        await db.user_wallets.insert_one(
            {"user_id": uid, "balance_eur": balance, "updated_at": utc_now()}
        )
        aid = ObjectId()
        await db.athletes.insert_one({
            "_id": aid, "sport_id": "calcio", "status": "ACTIVE", "role": "ATT",
            "display_label": "L. Test", "team_fantasy_id": ObjectId(),
            "prezzo_corrente_eur": price, "prezzo_iniziale_eur": price,
            "float_quote": 1_000_000, "primary_pool_qty": pool,
            "circulating_qty": 1_000_000 - pool,
        })
        return aid

    aid = asyncio.run(_seed())
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[current_user] = lambda: {
        "_id": uid, "email": "t@x.io", "status": "active", "role": "user"
    }
    return TestClient(app), str(aid)


def teardown_function():
    app.dependency_overrides.clear()


def test_buy_endpoint_ok():
    client, aid = _make_client()
    r = client.post("/api/market/orders", json={"athlete_id": aid, "side": "buy", "qty": 100})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["side"] == "buy"
    assert body["new_balance"] == 100.0 - 2.0 * 1.035

    h = client.get("/api/market/holdings").json()
    assert len(h) == 1
    assert h[0]["quantity"] == 100


def test_buy_insufficient_funds_returns_400():
    client, aid = _make_client(balance=1.0)
    r = client.post("/api/market/orders", json={"athlete_id": aid, "side": "buy", "qty": 100})
    assert r.status_code == 400
    assert r.json()["detail"]["error_code"] == "market.insufficient_funds"


def test_sell_before_holding_returns_400():
    client, aid = _make_client()
    client.post("/api/market/orders", json={"athlete_id": aid, "side": "buy", "qty": 100})
    r = client.post("/api/market/orders", json={"athlete_id": aid, "side": "sell", "qty": 10})
    assert r.status_code == 400
    assert r.json()["detail"]["error_code"] == "market.holding_locked"


def test_quote_endpoint():
    client, aid = _make_client()
    r = client.get(f"/api/market/athletes/{aid}/quote?qty=100")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["prezzo_corrente_eur"] == 0.02
    assert body["primary_pool_qty"] == 1_000_000
    assert body["buy_cost"] == 2.0 * 1.035
    assert body["sell_proceeds"] == 2.0 * 0.965
