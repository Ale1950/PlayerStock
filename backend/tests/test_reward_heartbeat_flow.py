"""RED→GREEN: flusso heartbeat DB (firma, anti-replay, rate-limit, accrual da attività)."""
from __future__ import annotations

import hashlib
import hmac
from datetime import timedelta

import pytest
from bson import ObjectId

from app.core.errors import APIError
from app.models.common import utc_now
from app.reward.internal import InternalRewardProvider
from app.reward.service import connect_wallet, process_heartbeat


class _Settings:
    REWARD_HEARTBEAT_SECRET = "test-secret"
    REWARD_HEARTBEAT_INTERVAL_SEC = 300
    REWARD_DAILY_CAP_NACKL = 50.0
    REWARD_BASE_PER_BEAT = 0.1
    REWARD_PER_ACTIVITY = 1.0


def _sig(uid, nonce, ts, secret="test-secret"):
    msg = f"{uid}:{nonce}:{ts}"
    return msg, hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()


async def _seed_orders(db, uid, n, now):
    if n:
        await db.orders.insert_many(
            [{"user_id": uid, "side": "buy", "qty": 1, "created_at": now} for _ in range(n)]
        )


async def test_heartbeat_accrues_from_observed_activity(mock_db):
    uid = ObjectId()
    now = utc_now()
    await _seed_orders(mock_db, uid, 3, now)  # 3 ordini reali nella finestra
    nonce = "n1"; ts = int(now.timestamp())
    _, sig = _sig(uid, nonce, ts)
    res = await process_heartbeat(mock_db, InternalRewardProvider(), _Settings(),
                                  user_id=uid, nonce=nonce, ts=ts, signature=sig, now=now)
    assert res["accrued"] == pytest.approx(0.1 + 3 * 1.0)  # base + 3 attività
    assert res["balance"]["amount"] == pytest.approx(res["accrued"])
    assert res["balance"]["is_placeholder"] is True


async def test_heartbeat_bad_signature_401(mock_db):
    uid = ObjectId(); now = utc_now()
    with pytest.raises(APIError) as e:
        await process_heartbeat(mock_db, InternalRewardProvider(), _Settings(),
                                user_id=uid, nonce="x", ts=int(now.timestamp()),
                                signature="bad", now=now)
    assert e.value.status_code == 401


async def test_heartbeat_anti_replay_409(mock_db):
    uid = ObjectId(); now = utc_now()
    nonce = "dup"; ts = int(now.timestamp())
    _, sig = _sig(uid, nonce, ts)
    await process_heartbeat(mock_db, InternalRewardProvider(), _Settings(),
                            user_id=uid, nonce=nonce, ts=ts, signature=sig, now=now)
    later = now + timedelta(seconds=600)  # supera il rate-limit, ma nonce riusato
    with pytest.raises(APIError) as e:
        await process_heartbeat(mock_db, InternalRewardProvider(), _Settings(),
                                user_id=uid, nonce=nonce, ts=ts, signature=sig, now=later)
    assert e.value.status_code == 409


async def test_heartbeat_rate_limited_429(mock_db):
    uid = ObjectId(); now = utc_now()
    n1, s1 = "a", _sig(uid, "a", 1)[1]
    await process_heartbeat(mock_db, InternalRewardProvider(), _Settings(),
                            user_id=uid, nonce="a", ts=1, signature=s1, now=now)
    # secondo beat (nonce diverso) entro l'intervallo -> 429
    s2 = _sig(uid, "b", 2)[1]
    with pytest.raises(APIError) as e:
        await process_heartbeat(mock_db, InternalRewardProvider(), _Settings(),
                                user_id=uid, nonce="b", ts=2, signature=s2,
                                now=now + timedelta(seconds=10))
    assert e.value.status_code == 429


async def test_heartbeat_respects_daily_cap(mock_db):
    uid = ObjectId(); now = utc_now()
    # pre-accredita vicino al cap
    p = InternalRewardProvider()
    await p.accrue(mock_db, uid, amount=49.5, reason="seed", now=now)
    await _seed_orders(mock_db, uid, 100, now)
    _, sig = _sig(uid, "cap", 9)
    res = await process_heartbeat(mock_db, p, _Settings(),
                                  user_id=uid, nonce="cap", ts=9, signature=sig, now=now)
    assert res["accrued"] == pytest.approx(0.5)  # solo il residuo fino a 50
    assert res["balance"]["amount"] == pytest.approx(50.0)


async def test_connect_wallet_rejects_seed(mock_db):
    uid = ObjectId()
    with pytest.raises(APIError):
        await connect_wallet(mock_db, uid,
                             "legal winner thank year wave sausage worth useful legal winner thank yellow",
                             now=utc_now())


async def test_connect_wallet_stores_public_key(mock_db):
    uid = ObjectId()
    res = await connect_wallet(mock_db, uid, "0x" + "a" * 64, now=utc_now())
    assert res["connected"] is True
    w = await mock_db.reward_wallets.find_one({"user_id": uid})
    assert w["mining_public_key"] == "a" * 64
    assert "secret" not in w and "seed" not in w
