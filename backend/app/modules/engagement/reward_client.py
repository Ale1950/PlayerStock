"""RewardClient — adapter Engagement → RewardProvider (Fase 5).

DELEGA (no percorso parallelo): l'engagement NON scrive mai direttamente il saldo.
Tutto l'accrual passa dall'`InternalRewardProvider` di Fase 5 → unico percorso
`nackl_ledger` + `reward_balances.amount`, con `is_placeholder`. Così non c'è
split-brain tra il saldo engagement e `/api/reward/balance`.

Quando il NACKL reale on-chain sarà attivo (Q1/Q5), resterà comunque distinto: il
placeholder interno e il saldo on-chain (TestnetWalletRewardProvider) sono separati.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.models.common import utc_now
from app.reward.internal import InternalRewardProvider


class RewardClient:
    """Chiamato SOLO dal modulo engagement. Delega al RewardProvider interno."""

    def __init__(self, db) -> None:
        self.db = db
        self._provider = InternalRewardProvider()

    async def accrue(
        self, *, user_id, amount: float | Decimal, source: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict:
        """Accredita NACKL placeholder via RewardProvider. SOURCE deve iniziare con `engagement_`."""
        if not source.startswith("engagement_"):
            raise ValueError("engagement reward source must start with 'engagement_'")
        amt = float(Decimal(str(amount)))
        if amt <= 0:
            return {"ok": False, "reason": "amount must be > 0"}

        now = utc_now()
        new_balance = await self._provider.accrue(
            self.db, user_id, amount=amt, reason=source, now=now, metadata=metadata,
        )
        return {
            "ok": True,
            "tx_id": None,  # il ledger registra l'entry; nessun tx-id on-chain (placeholder)
            "new_balance": new_balance,
            "is_placeholder": self._provider.is_placeholder,
        }


def get_reward_client(db) -> RewardClient:
    return RewardClient(db)
