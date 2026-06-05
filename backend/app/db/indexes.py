"""MongoDB indexes creation (idempotent, run at startup)."""
from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create indexes for all collections. Idempotent."""

    # ─── users ───
    await db.users.create_index("google_sub", unique=True)
    await db.users.create_index("email", unique=True)
    await db.users.create_index("status")

    # ─── user_wallets ───
    await db.user_wallets.create_index("user_id", unique=True)

    # ─── wallet_transactions ───
    await db.wallet_transactions.create_index([("user_id", 1), ("created_at", -1)])
    await db.wallet_transactions.create_index("type")

    # ─── teams_fantasy ───
    await db.teams_fantasy.create_index([("sport_id", 1), ("internal_real_id", 1)], unique=True)
    await db.teams_fantasy.create_index("fantasy_name")

    # ─── athletes ───
    await db.athletes.create_index([("sport_id", 1), ("role", 1)])
    await db.athletes.create_index("team_fantasy_id")
    await db.athletes.create_index("status")
    await db.athletes.create_index([("sport_id", 1), ("internal_full_name", 1), ("team_fantasy_id", 1)],
                                    unique=True, name="ux_athlete_dedup")

    # ─── holdings (Fase 3) ───
    await db.holdings.create_index([("user_id", 1), ("athlete_id", 1)], unique=True)
    await db.holdings.create_index("athlete_id")

    # ─── orders (Fase 3) ───
    await db.orders.create_index([("user_id", 1), ("created_at", -1)])
    await db.orders.create_index([("athlete_id", 1), ("created_at", -1)])

    # ─── trades (Fase 3) ───
    await db.trades.create_index([("athlete_id", 1), ("ts", -1)])

    # ─── price_history (Fase 2b/3 — sparkline) ───
    await db.price_history.create_index([("athlete_id", 1), ("ts", 1)])

    # ─── reward NACKL (Fase 5) ───
    await db.reward_balances.create_index("user_id", unique=True)
    await db.reward_wallets.create_index("user_id", unique=True)
    await db.reward_state.create_index("user_id", unique=True)
    await db.heartbeat_nonces.create_index([("user_id", 1), ("nonce", 1)], unique=True)
    await db.nackl_ledger.create_index([("user_id", 1), ("ts", -1)])

    # ─── events (schema-only Fase 1) ───
    await db.events.create_index([("athlete_id", 1), ("season", 1), ("matchday", 1)])

    # ─── data_sync_log ───
    await db.data_sync_log.create_index([("source", 1), ("ran_at", -1)])

    logger.info("MongoDB indexes ensured")
