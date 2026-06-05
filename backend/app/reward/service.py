"""Servizio reward DB: heartbeat (firma+anti-replay+rate-limit+accrual) e wallet connect.

Accrual = PLACEHOLDER (Internal). Legato all'ATTIVITÀ osservata dal server (ordini reali
nella finestra) + piccola base passiva, limitato dal cap giornaliero conservativo.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.errors import err_bad_request, err_conflict, err_too_many, err_unauthorized
from app.reward.base import RewardProvider
from app.reward.heartbeat import compute_accrual, verify_signature
from app.reward.wallet import validate_mining_public_key


def _start_of_day(now: datetime) -> datetime:
    n = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    return n.replace(hour=0, minute=0, second=0, microsecond=0)


async def _accrued_today(db, user_id, now: datetime) -> float:
    cur = db.nackl_ledger.aggregate([
        {"$match": {"user_id": user_id, "ts": {"$gte": _start_of_day(now)}}},
        {"$group": {"_id": None, "tot": {"$sum": "$amount"}}},
    ])
    rows = await cur.to_list(length=1)
    return float(rows[0]["tot"]) if rows else 0.0


async def process_heartbeat(
    db, provider: RewardProvider, settings, *,
    user_id, nonce: str, ts: int, signature: str, now: datetime,
) -> dict:
    # 1. firma HMAC
    message = f"{user_id}:{nonce}:{ts}"
    if not verify_signature(message, signature, settings.REWARD_HEARTBEAT_SECRET):
        raise err_unauthorized("reward.heartbeat.bad_signature", "Firma heartbeat non valida")

    # 2. anti-replay (nonce per utente)
    if await db.heartbeat_nonces.find_one({"user_id": user_id, "nonce": nonce}):
        raise err_conflict("reward.heartbeat.replay", "Heartbeat già ricevuto (nonce riusato)")

    # 3. rate-limit (intervallo minimo tra beat)
    state = await db.reward_state.find_one({"user_id": user_id})
    last = state.get("last_heartbeat_at") if state else None
    since = now - timedelta(seconds=settings.REWARD_HEARTBEAT_INTERVAL_SEC)
    if last is not None:
        last_aware = last if last.tzinfo else last.replace(tzinfo=timezone.utc)
        now_aware = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
        if (now_aware - last_aware).total_seconds() < settings.REWARD_HEARTBEAT_INTERVAL_SEC:
            raise err_too_many("reward.heartbeat.rate_limited", "Heartbeat troppo frequente")
        since = last_aware

    # 4. attività osservata dal server (ordini reali nella finestra)
    activity_count = await db.orders.count_documents({"user_id": user_id, "created_at": {"$gt": since}})

    # 5. accrual placeholder, limitato dal cap giornaliero
    amount = 0.0
    if provider.is_placeholder:
        accrued = await _accrued_today(db, user_id, now)
        amount = compute_accrual(
            activity_count=activity_count, accrued_today=accrued,
            daily_cap=settings.REWARD_DAILY_CAP_NACKL,
            base_per_beat=settings.REWARD_BASE_PER_BEAT,
            per_activity=settings.REWARD_PER_ACTIVITY,
        )
        if amount > 0:
            await provider.accrue(db, user_id, amount=amount, reason="heartbeat", now=now)

    # 6. registra nonce + aggiorna stato
    await db.heartbeat_nonces.insert_one({"user_id": user_id, "nonce": nonce, "ts": now})
    await db.reward_state.update_one(
        {"user_id": user_id},
        {"$set": {"last_heartbeat_at": now}, "$setOnInsert": {"user_id": user_id}},
        upsert=True,
    )

    balance = await provider.balance(db, user_id)
    return {"accrued": amount, "activity_count": activity_count, "balance": balance}


async def connect_wallet(db, user_id, raw_key: str, now: datetime) -> dict:
    """Salva SOLO la mining public key (rifiuta seed/chiavi di spesa)."""
    pub = validate_mining_public_key(raw_key)
    await db.reward_wallets.update_one(
        {"user_id": user_id},
        {"$set": {"mining_public_key": pub, "connected_at": now},
         "$setOnInsert": {"user_id": user_id}},
        upsert=True,
    )
    return {"connected": True, "mining_public_key_preview": pub[:8] + "…"}
