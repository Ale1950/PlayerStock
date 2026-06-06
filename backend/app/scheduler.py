"""Scheduler job (APScheduler) — fondamenta per i job ricorrenti.

Oggi: settle delle predizioni scadute ogni 5 min (Fase 6).
Futuri: tick prezzi (mercato%), reset cap giornaliero reward, ecc.

⚠️ PROD multi-worker: avviare lo scheduler in UN SOLO processo (es. flag env o
worker dedicato), altrimenti i job partono N volte. In MVP single-process è ok.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config.pricing_constants import SNAPSHOT_PRICE_INTERVALLO_MIN
from app.market.trade import snapshot_all_active_prices
from app.modules.engagement.service import settle_expired_predictions

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def start_scheduler(db) -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    sched = AsyncIOScheduler()

    async def _settle_job() -> None:
        try:
            res = await settle_expired_predictions(db)
            if res.get("settled"):
                logger.info("settle_predictions: %s", res)
        except Exception as e:  # noqa: BLE001
            logger.warning("settle_predictions job error: %s", e)

    async def _snapshot_job() -> None:
        try:
            n = await snapshot_all_active_prices(db)
            logger.info("snapshot_prices: %d atleti", n)
        except Exception as e:  # noqa: BLE001
            logger.warning("snapshot_prices job error: %s", e)

    sched.add_job(
        _settle_job, "interval", minutes=5, id="settle_predictions",
        max_instances=1, coalesce=True,
    )
    sched.add_job(
        _snapshot_job, "interval", minutes=SNAPSHOT_PRICE_INTERVALLO_MIN,
        id="snapshot_prices", max_instances=1, coalesce=True,
    )
    sched.start()
    _scheduler = sched
    logger.info(
        "APScheduler avviato (settle ogni 5 min · snapshot prezzi ogni %d min)",
        SNAPSHOT_PRICE_INTERVALLO_MIN,
    )
    return sched


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("APScheduler fermato")
