"""TDD: missioni + sfida settimanale + premio fisso a cap.

Premi su LEDGER SEPARATI (Crediti via faucet-cap / NACKL via RewardProvider), idempotenti.
VALORI premio = PROPOSTI (da approvare); qui si testa il MECCANISMO, non i valori finali.
"""
from __future__ import annotations

import datetime as dt

import pytest
from bson import ObjectId

from app.economy.credit_faucet import grant_fixed_credits
from app.models.common import utc_now
from app.modules.engagement.missions import (
    MISSIONS,
    claim_mission,
    evaluate_missions,
)
from app.modules.engagement.challenges import settle_weekly_challenge, weekly_challenge
from app.reward.internal import InternalRewardProvider


# ───────── premio fisso a cap (ledger Crediti) ─────────
async def test_grant_fixed_credits_idempotent_and_capped(mock_db):
    uid = ObjectId()
    await mock_db.user_wallets.insert_one({"user_id": uid, "balance_eur": 100.0, "updated_at": utc_now()})
    now = dt.datetime(2026, 1, 1, 12, 0)
    r1 = await grant_fixed_credits(mock_db, user_id=uid, event_id="m1", amount=8.0, now=now, daily_cap=5.0)
    assert r1["credits"] == pytest.approx(5.0)  # cap giornaliero
    r2 = await grant_fixed_credits(mock_db, user_id=uid, event_id="m1", amount=8.0, now=now, daily_cap=5.0)
    assert r2["idempotent"] is True
    w = await mock_db.user_wallets.find_one({"user_id": uid})
    assert w["balance_eur"] == pytest.approx(105.0)  # accreditato UNA volta, capped


# ───────── missioni ─────────
async def _holding(db, uid, role, qty=10, days_ago=0):
    aid = ObjectId()
    await db.athletes.insert_one({"_id": aid, "status": "ACTIVE", "role": role, "prezzo_corrente_eur": 0.03,
                                  "prezzo_iniziale_eur": 0.01, "float_quote": 1_000_000})
    await db.holdings.insert_one({"user_id": uid, "athlete_id": aid, "quantity": qty,
                                  "lots": [{"qty": qty, "price": 0.02, "acquired_at": utc_now() - dt.timedelta(days=days_ago)}]})
    return aid


async def test_evaluate_missions_progress(mock_db):
    uid = ObjectId()
    await mock_db.user_wallets.insert_one({"user_id": uid, "balance_eur": 100.0, "updated_at": utc_now()})
    await _holding(mock_db, uid, "ATT")
    await _holding(mock_db, uid, "CC")
    ms = {m["id"]: m for m in await evaluate_missions(mock_db, uid)}
    assert ms["first_buy"]["completed"] is True
    assert ms["diversify_roles"]["progress"] == 2 and ms["diversify_roles"]["completed"] is False
    assert all("reward_proposed" in m for m in ms.values())


async def test_claim_mission_idempotent_separate_ledgers(mock_db):
    uid = ObjectId()
    await mock_db.user_wallets.insert_one({"user_id": uid, "balance_eur": 100.0, "updated_at": utc_now()})
    await _holding(mock_db, uid, "ATT")
    r1 = await claim_mission(mock_db, uid, "first_buy")
    assert r1["claimed"] is True and r1["credits"] > 0 and r1["nackl"] > 0
    # NACKL sul SUO ledger
    bal = await InternalRewardProvider().balance(mock_db, uid)
    assert bal["amount"] == pytest.approx(r1["nackl"])
    # idempotente
    r2 = await claim_mission(mock_db, uid, "first_buy")
    assert r2["claimed"] is False and r2.get("already") is True
    assert await mock_db.mission_claims.count_documents({}) == 1


async def test_claim_incomplete_mission_blocked(mock_db):
    uid = ObjectId()
    await mock_db.user_wallets.insert_one({"user_id": uid, "balance_eur": 100.0, "updated_at": utc_now()})
    r = await claim_mission(mock_db, uid, "reach_15k")  # nessun patrimonio
    assert r["claimed"] is False


# ───────── sfida settimanale ─────────
async def test_weekly_challenge_and_settle(mock_db):
    u1, u2 = ObjectId(), ObjectId()
    for u, bal in ((u1, 1000.0), (u2, 50.0)):
        await mock_db.user_wallets.insert_one({"user_id": u, "balance_eur": bal, "updated_at": utc_now()})
        await mock_db.users.insert_one({"_id": u, "name": "Tester One" if u == u1 else "Tester Two", "status": "active"})
    a1 = await _holding(mock_db, u1, "ATT", qty=10000)
    await mock_db.holdings.insert_one({"user_id": u2, "athlete_id": a1, "quantity": 100,
                                       "lots": [{"qty": 100, "price": 0.02, "acquired_at": utc_now()}]})
    for d in (10, 1):
        await mock_db.price_history.insert_one({"athlete_id": a1, "prezzo": 0.02 + d * 0.0001, "ts": utc_now() - dt.timedelta(days=d)})

    ch = await weekly_challenge(mock_db, u1)
    assert "week_key" in ch and "standings" in ch and ch["my_rank"] is not None
    assert all("pseudonym" in s and "name" not in s for s in ch["standings"])  # solo pseudonimi

    res = await settle_weekly_challenge(mock_db, ch["week_key"])
    assert res["winners"] >= 1
    # idempotente
    res2 = await settle_weekly_challenge(mock_db, ch["week_key"])
    assert res2["winners"] == 0
