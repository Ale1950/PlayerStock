"""InternalRewardProvider — saldo PLACEHOLDER (dev/MVP), NON NACKL reale.

Scrive su `nackl_ledger` (immutabile, append-only) e `reward_balances`. Da non
presentare all'utente come NACKL reale guadagnato: serve a dar vita all'MVP finché
il miner on-chain non è attivo (Q1/Q5).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.reward.base import RewardProvider


class InternalRewardProvider(RewardProvider):
    provider_name = "internal_placeholder"
    is_placeholder = True

    async def can_earn(self, db, user_id, *, now: datetime) -> bool:
        return True

    async def accrue(self, db, user_id, *, amount: float, reason: str, now: datetime) -> float:
        if amount <= 0:
            cur = await self.balance(db, user_id)
            return cur["amount"]
        await db.nackl_ledger.insert_one({
            "user_id": user_id, "amount": float(amount), "reason": reason,
            "placeholder": True, "ts": now,
        })
        await db.reward_balances.update_one(
            {"user_id": user_id},
            {"$inc": {"amount": float(amount)}, "$set": {"updated_at": now},
             "$setOnInsert": {"user_id": user_id, "currency": "NACKL"}},
            upsert=True,
        )
        return (await self.balance(db, user_id))["amount"]

    async def balance(self, db, user_id) -> dict[str, Any]:
        doc = await db.reward_balances.find_one({"user_id": user_id})
        return {
            "amount": float(doc["amount"]) if doc else 0.0,
            "currency": "NACKL",
            "source": self.provider_name,
            "is_placeholder": True,
        }
