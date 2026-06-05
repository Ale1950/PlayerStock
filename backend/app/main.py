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
from app.modules.player import routes as player_routes
from app.modules.user import routes as user_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = get_db()
    await ensure_indexes(db)
    await run_all_seeds(db)
    logger.info("PlayerStock backend started")
    yield
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
        return {"status": "ok", "app": "PlayerStock", "version": "0.1.0-fase1"}

    api.include_router(auth_routes.router)
    api.include_router(user_routes.router)
    api.include_router(player_routes.router)
    api.include_router(admin_routes.router)

    app.include_router(api)

    return app


app = create_app()
