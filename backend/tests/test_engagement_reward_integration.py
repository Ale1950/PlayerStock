"""RED→GREEN: l'accrual engagement passa dal RewardProvider (no split-brain).

Completo un quiz → il saldo letto da InternalRewardProvider.balance (stessa fonte di
/api/reward/balance) riflette il reward. Nessun campo parallelo `nackl_balance`.
"""
from __future__ import annotations

import pytest
from bson import ObjectId

from app.models.common import utc_now
from app.modules.engagement.service import claim_daily_streak, submit_quiz_attempt
from app.reward.internal import InternalRewardProvider


async def test_quiz_reward_reflected_in_reward_provider_balance(mock_db):
    uid = ObjectId()
    quiz = await mock_db.quizzes.insert_one({
        "title": "T", "active": True, "created_at": utc_now(),
        "questions": [{"text": "q", "options": ["a", "b"], "correct_index": 1}],
    })
    res = await submit_quiz_attempt(mock_db, uid, quiz_id=str(quiz.inserted_id), answers=[1])
    assert res["ok"] and res["reward_amount"] == pytest.approx(1.5)  # 0.5 + 1.0 perfect

    # UNICA fonte: il saldo del RewardProvider riflette il reward engagement
    bal = await InternalRewardProvider().balance(mock_db, uid)
    assert bal["amount"] == pytest.approx(res["reward_amount"])
    assert bal["is_placeholder"] is True

    # ledger scritto via provider (reason = source engagement_*)
    led = await mock_db.nackl_ledger.find_one({"user_id": uid})
    assert led["reason"] == "engagement_quiz"
    assert led.get("metadata", {}).get("quiz_id")

    # nessun percorso parallelo: niente campo nackl_balance
    rb = await mock_db.reward_balances.find_one({"user_id": uid})
    assert "amount" in rb and "nackl_balance" not in rb


async def test_streak_reward_accumulates_in_same_balance(mock_db):
    uid = ObjectId()
    s = await claim_daily_streak(mock_db, uid)
    assert s["claimed"] and s["reward_amount"] == pytest.approx(1.0)
    bal = await InternalRewardProvider().balance(mock_db, uid)
    assert bal["amount"] == pytest.approx(1.0)
