"""Interfaccia astratta RewardProvider (spec §7)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class RewardProvider(ABC):
    """Astrazione per l'accredito/lettura del reward NACKL.

    `is_placeholder=True` → saldo NON reale (InternalRewardProvider, dev/MVP).
    `is_placeholder=False` → rappresenta NACKL reale on-chain (TestnetWallet/Mainnet).
    """

    provider_name: str
    is_placeholder: bool = False

    @abstractmethod
    async def can_earn(self, db, user_id, *, now: datetime) -> bool:
        """True se l'utente può accumulare reward tramite questo provider."""

    @abstractmethod
    async def accrue(self, db, user_id, *, amount: float, reason: str, now: datetime) -> float:
        """Accredita `amount` e ritorna il nuovo saldo."""

    @abstractmethod
    async def balance(self, db, user_id) -> dict[str, Any]:
        """Saldo corrente: {amount, currency, source, is_placeholder, ...}."""
