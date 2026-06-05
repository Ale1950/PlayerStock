"""TestnetWalletRewardProvider — scaffold INERTE per Acki Nacki shellnet.

Il NACKL reale è emesso dal PROTOCOLLO: l'app NON lo accredita. Questo provider:
- NON accredita (accrue è no-op: `can_earn` = False);
- legge il saldo on-chain in sola lettura via GraphQL (quando configurato).

Finché Q1 (`app_dapp_id`) e Q5 (mining key/wallet di test) non sono sciolte, o manca
l'endpoint, il provider è un NO-OP robusto: `status="pending_credentials"`, saldo 0.
La submission/lettura on-chain reale (bee_sdk WASM + @eversdk in WebView) arriva dopo.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.reward.base import RewardProvider


class TestnetWalletRewardProvider(RewardProvider):
    provider_name = "testnet_shellnet"
    is_placeholder = False  # rappresenta NACKL reale (on-chain), non placeholder
    __test__ = False  # non è una classe di test (evita warning pytest sul prefisso "Test")

    def __init__(self, *, app_id: str = "", graphql_endpoint: str = "", network: str = "shellnet") -> None:
        self.app_id = app_id
        self.graphql_endpoint = graphql_endpoint
        self.network = network

    def _configured(self) -> bool:
        """Q1/Q5 sciolte? app_id reale + endpoint presenti."""
        placeholder_app = (not self.app_id) or set(self.app_id.replace("0x", "")) <= {"0"}
        return bool(self.graphql_endpoint) and not placeholder_app

    async def can_earn(self, db, user_id, *, now: datetime) -> bool:
        return False  # l'app non emette NACKL reale

    async def accrue(self, db, user_id, *, amount: float, reason: str, now: datetime) -> float:
        # No-op: nessun accredito off-chain di NACKL reale.
        return (await self.balance(db, user_id))["amount"]

    async def balance(self, db, user_id) -> dict[str, Any]:
        if not self._configured():
            return {
                "amount": 0.0, "currency": "NACKL", "source": self.provider_name,
                "is_placeholder": False, "status": "pending_credentials",
                "network": self.network,
            }
        # TODO Q1/Q5: lettura on-chain via @eversdk GraphQL (self.graphql_endpoint).
        # Per ora, anche se "configurato", restiamo read-only senza wallet collegato.
        wallet = await db.reward_wallets.find_one({"user_id": user_id})
        return {
            "amount": 0.0, "currency": "NACKL", "source": self.provider_name,
            "is_placeholder": False,
            "status": "ready" if wallet else "no_wallet",
            "network": self.network,
        }
