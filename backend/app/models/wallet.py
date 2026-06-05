"""Wallet-related Pydantic models."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.common import PyObjectId

WalletTxType = Literal[
    "welcome_bonus",
    "daily_reward",
    "trade_buy",
    "trade_sell",
    "fee_buyer",
    "fee_seller",
    "refund_transfer",
    "engagement_reward",
    "adjustment",
]


class WalletTransactionPublic(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    type: WalletTxType
    amount: float
    balance_after: float
    description_it: str
    created_at: datetime

    model_config = {"populate_by_name": True}


class WalletTransactionList(BaseModel):
    items: list[WalletTransactionPublic]
    total: int
    page: int
    page_size: int
