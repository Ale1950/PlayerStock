"""TDD: gli eventi engagement accreditano SOLO € (faucet), MAI NACKL.

Vincolo permanente: il gioco non assegna NACKL (i NACKL derivano solo dal mining).
Ogni evento engagement accredita € (faucet, event_id stabile/idempotente) e lascia
il ledger NACKL a ZERO.
"""
from __future__ import annotations

import datetime as dt

import pytest
from bson import ObjectId

from app.models.common import utc_now
from app.modules.engagement.service import (
    claim_daily_streak,
    settle_expired_predictions,
    submit_quiz_attempt,
)
from app.reward.internal import InternalRewardProvider


async def _credits(db, uid) -> float:
    w = await db.user_wallets.find_one({"user_id": uid})
    return float(w["balance_eur"]) if w else 0.0


# ───────────────────────── STREAK ─────────────────────────
async def test_streak_grants_credits_and_keeps_nackl(mock_db):
    uid = ObjectId()
    res = await claim_daily_streak(mock_db, uid)
    assert res["claimed"]
    # € accreditati dal faucet (D7 ×100: EP=1.0 → 1×3×25 = 75)
    assert res["credit_bonus"] == pytest.approx(75.0)
    assert await _credits(mock_db, uid) == pytest.approx(75.0)
    assert await mock_db.engagement_credit_grants.count_documents({}) == 1
    # NACKL NON accreditato dall'engagement (solo mining): resta a 0
    bal = await InternalRewardProvider().balance(mock_db, uid)
    assert bal["amount"] == pytest.approx(0.0)


async def test_streak_same_day_no_double_credit(mock_db):
    uid = ObjectId()
    await claim_daily_streak(mock_db, uid)
    r2 = await claim_daily_streak(mock_db, uid)
    assert r2["claimed"] is False
    assert await mock_db.engagement_credit_grants.count_documents({}) == 1
    assert await _credits(mock_db, uid) == pytest.approx(75.0)


# ───────────────────────── QUIZ ─────────────────────────
async def _quiz(db):
    q = await db.quizzes.insert_one({
        "title": "T", "active": True, "created_at": utc_now(),
        "questions": [{"text": "q", "options": ["a", "b"], "correct_index": 1}],
    })
    return str(q.inserted_id)


async def test_quiz_grants_credits_and_keeps_nackl(mock_db):
    uid = ObjectId()
    qid = await _quiz(mock_db)
    res = await submit_quiz_attempt(mock_db, uid, quiz_id=qid, answers=[1])
    assert res["ok"]
    # EP = reward 1.5 → 1.5×3×25 = 112.5 € (D7 ×100)
    assert res["credit_bonus"] == pytest.approx(112.5)
    assert await mock_db.engagement_credit_grants.count_documents({}) == 1
    bal = await InternalRewardProvider().balance(mock_db, uid)
    assert bal["amount"] == pytest.approx(0.0)  # NACKL mai da engagement


async def test_quiz_reattempt_no_double_credit(mock_db):
    uid = ObjectId()
    qid = await _quiz(mock_db)
    await submit_quiz_attempt(mock_db, uid, quiz_id=qid, answers=[1])
    r2 = await submit_quiz_attempt(mock_db, uid, quiz_id=qid, answers=[1])
    assert r2["ok"] is False  # già tentato
    assert await mock_db.engagement_credit_grants.count_documents({}) == 1


# ───────────────────────── PREDICTION ─────────────────────────
async def test_prediction_settle_grants_credits_idempotent(mock_db):
    uid = ObjectId()
    aid = ObjectId()
    await mock_db.athletes.insert_one({
        "_id": aid, "sport_id": "calcio", "status": "ACTIVE", "role": "ATT",
        "prezzo_corrente_eur": 0.03, "prezzo_iniziale_eur": 0.01,
    })
    past = utc_now() - dt.timedelta(hours=1)
    await mock_db.predictions.insert_one({
        "user_id": uid, "athlete_id": aid, "direction": "up", "base_price": 0.01,
        "horizon_hours": 24, "status": "open", "created_at": past - dt.timedelta(hours=24),
        "expires_at": past, "settled_at": None, "settled_price": None, "outcome": None,
        "reward_tx_id": None, "reward_amount": 0.0,
    })
    out = await settle_expired_predictions(mock_db)
    assert out["won"] == 1
    # EP = 2.5 → 2.5×3×25 = 187.5 € (D7 ×100)
    assert await _credits(mock_db, uid) == pytest.approx(187.5)
    assert await mock_db.engagement_credit_grants.count_documents({}) == 1
    bal = await InternalRewardProvider().balance(mock_db, uid)
    assert bal["amount"] == pytest.approx(0.0)  # NACKL mai da engagement
    # re-settle: niente di nuovo (predizione già chiusa) → nessun doppio credito
    out2 = await settle_expired_predictions(mock_db)
    assert out2["settled"] == 0
    assert await mock_db.engagement_credit_grants.count_documents({}) == 1
