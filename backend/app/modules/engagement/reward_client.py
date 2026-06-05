"""RewardProvider adapter — Fase 6 ENGAGEMENT.

Questo modulo NON implementa il reward (è Fase 5 di Claude Code).
Implementa SOLO un'INTERFACCIA STABILE che il modulo engagement chiama.

CLAUDE CODE, IN FASE DI MERGE:
  Sostituisci `_StubRewardProvider` con import del provider reale di Fase 5.
  La firma assunta è:

      async def accrue(
          *, user_id: ObjectId, amount: Decimal, source: str,
          metadata: dict | None = None,
      ) -> dict  # { "ok": bool, "tx_id": str, "new_balance": float, "is_placeholder": bool }

  Se la tua firma reale differisce, basta adattare `RewardClient.accrue` sotto.

Stub: scrive direttamente su `nackl_ledger` + `reward_balances` (collezioni Fase 5
secondo prompt) marcando `is_placeholder=True`. Non c'è cash-out, non è on-chain.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.models.common import utc_now


class RewardClient:
    """Interfaccia chiamata SOLO dal modulo engagement. Mai mescolare con Crediti."""

    def __init__(self, db) -> None:
        self.db = db

    async def accrue(
        self, *, user_id, amount: float | Decimal, source: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict:
        """Accredita NACKL placeholder all'utente. SOURCE deve iniziare con `engagement_`."""
        if not source.startswith("engagement_"):
            raise ValueError("engagement reward source must start with 'engagement_'")
        amt = float(Decimal(str(amount)))
        if amt <= 0:
            return {"ok": False, "reason": "amount must be > 0"}

        # === BEGIN STUB (Claude Code: sostituisci con provider reale Fase 5) ===
        now = utc_now()
        ledger_entry = {
            "user_id": user_id,
            "amount": amt,
            "source": source,
            "metadata": metadata or {},
            "is_placeholder": True,
            "created_at": now,
        }
        result = await self.db.nackl_ledger.insert_one(ledger_entry)
        update = await self.db.reward_balances.find_one_and_update(
            {"user_id": user_id},
            {"$inc": {"nackl_balance": amt}, "$set": {"updated_at": now},
             "$setOnInsert": {"user_id": user_id, "created_at": now}},
            upsert=True, return_document=True,
        )
        new_balance = float(update.get("nackl_balance", amt)) if update else amt
        return {
            "ok": True, "tx_id": str(result.inserted_id),
            "new_balance": new_balance, "is_placeholder": True,
        }
        # === END STUB ===


def get_reward_client(db) -> RewardClient:
    return RewardClient(db)
