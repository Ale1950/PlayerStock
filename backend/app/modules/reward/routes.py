"""Reward module (Fase 5): saldo NACKL, provider, wallet connect, heartbeat.

NACKL separato dai Crediti. Il saldo interno è un PLACEHOLDER (is_placeholder=True);
il NACKL reale arriva on-chain quando il miner è attivo (Q1/Q5).
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.deps import CurrentUserDep, DBDep, SettingsDep
from app.models.common import utc_now
from app.reward.factory import get_reward_provider
from app.reward.service import connect_wallet, process_heartbeat

router = APIRouter(tags=["reward"])


class WalletConnectRequest(BaseModel):
    mining_public_key: str = Field(..., description="Mining PUBLIC key (mai seed/segreta)")


class HeartbeatRequest(BaseModel):
    nonce: str
    ts: int
    signature: str


@router.get("/reward/balance")
async def reward_balance(user: CurrentUserDep, db: DBDep, settings: SettingsDep) -> dict:
    provider = get_reward_provider(settings)
    return await provider.balance(db, user["_id"])


@router.get("/reward/provider")
async def reward_provider_info(user: CurrentUserDep, db: DBDep, settings: SettingsDep) -> dict:
    provider = get_reward_provider(settings)
    wallet = await db.reward_wallets.find_one({"user_id": user["_id"]})
    return {
        "provider_name": provider.provider_name,
        "is_placeholder": provider.is_placeholder,
        "network": getattr(settings, "AN_NETWORK", "shellnet"),
        "wallet_connected": wallet is not None,
        "mining_status": "coming_soon",  # miner on-chain dipende da Q1/Q5
    }


@router.post("/reward/wallet/connect")
async def reward_wallet_connect(
    req: WalletConnectRequest, user: CurrentUserDep, db: DBDep
) -> dict:
    return await connect_wallet(db, user["_id"], req.mining_public_key, utc_now())


@router.post("/reward/heartbeat")
async def reward_heartbeat(
    req: HeartbeatRequest, user: CurrentUserDep, db: DBDep, settings: SettingsDep
) -> dict:
    provider = get_reward_provider(settings)
    return await process_heartbeat(
        db, provider, settings,
        user_id=user["_id"], nonce=req.nonce, ts=req.ts, signature=req.signature, now=utc_now(),
    )
