"""FastAPI app factory + lifespan + router mounting."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.core.db import close_db, get_db, init_db
from app.db.indexes import ensure_indexes
from app.db.seed import run_all_seeds
from app.modules.admin import routes as admin_routes
from app.modules.auth import routes as auth_routes
from app.modules.engagement import routes as engagement_routes
from app.modules.market import routes as market_routes
from app.modules.player import routes as player_routes
from app.modules.portfolio import routes as portfolio_routes
from app.modules.reward import routes as reward_routes
from app.modules.stats import routes as stats_routes
from app.modules.user import routes as user_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = get_db()
    # RESILIENZA: index/seed sono IDEMPOTENTI e Atlas è già seedato → se Atlas ha un
    # blip TLS all'avvio NON facciamo morire l'app. Si parte "degradati" e motor
    # riconnette da solo quando Atlas torna (era una debolezza nota — DECISIONS).
    try:
        await ensure_indexes(db)
        await run_all_seeds(db)
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "Startup DB init SALTATO (Atlas non raggiungibile?): %s — app avviata in modalità "
            "degradata, riconnessione automatica.", e,
        )
    from app.scheduler import shutdown_scheduler, start_scheduler
    try:
        start_scheduler(db)  # job ricorrenti. PROD: 1 solo processo.
    except Exception as e:  # noqa: BLE001
        logger.warning("Scheduler non avviato: %s", e)
    logger.info("PlayerStock backend started")
    yield
    shutdown_scheduler()
    close_db()
    logger.info("PlayerStock backend stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="PlayerStock API",
        version="0.1.0-fase1",
        description="Borsa virtuale degli atleti — backend MVP",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = APIRouter(prefix=settings.API_PREFIX)

    @api.get("/health")
    async def health():
        # Non crasha mai: riporta lo stato DB (ok/degraded) senza far cadere l'app.
        from app.core.db import db_health
        return {"status": "ok", "app": "PlayerStock", "version": "0.1.0-fase1",
                "db": await db_health()}

    api.include_router(auth_routes.router)
    api.include_router(user_routes.router)
    api.include_router(player_routes.router)
    api.include_router(market_routes.router)
    api.include_router(portfolio_routes.router)
    api.include_router(reward_routes.router)
    api.include_router(engagement_routes.router)
    api.include_router(admin_routes.router)
    api.include_router(stats_routes.router)

    app.include_router(api)

    return app


app = create_app()
