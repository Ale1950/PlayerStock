"""CLI: esegue N round di performance (D10) sul DB — semina/demo del prezzo vivo.

Usa il feed a innesto + il gain da settings (default veloce). Muove il prezzo equo,
accumula stat stagionali, scrive round_events. Per il go-live: `--seed` = ultime 10
giornate della stagione precedente (storia non piatta).

Uso (dalla cartella backend/):
    python -m app.cli.run_rounds --rounds 6
    python -m app.cli.run_rounds --seed            # 10 round (stagione precedente)
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import statistics as st
import sys

from app.config.settings import get_settings
from app.core.db import close_db, get_db, init_db
from app.market.rounds import run_round, seed_previous_season
from app.pricing.feed import get_performance_feed

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_rounds")


async def main(rounds: int, gain: float | None, seed: bool) -> int:
    init_db()
    db = get_db()
    settings = get_settings()
    feed = get_performance_feed(settings)
    g = gain if gain is not None else settings.PERF_PRICE_GAIN

    if seed:
        rep = await seed_previous_season(db, feed=feed, rounds=10, gain=g)
        logger.info("seed stagione precedente: %s (gain=%s, feed=%s)", rep, g, feed.name)
    else:
        last = {}
        for _ in range(rounds):
            last = await run_round(db, feed=feed, gain=g)
        logger.info("eseguiti %d round (gain=%s) → round corrente %s",
                    rounds, g, last.get("round"))
        for m in last.get("top_up", [])[:3]:
            logger.info("  ▲ %-12s %+.2f%% (%s)", m["label"], m["perf_pct"] * 100, m["reason"])
        for m in last.get("top_down", [])[:3]:
            logger.info("  ▼ %-12s %+.2f%% (%s)", m["label"], m["perf_pct"] * 100, m["reason"])

    docs = await db.athletes.find({"status": "ACTIVE"}).to_list(length=100000)
    prices = sorted(float(d["prezzo_corrente_eur"]) for d in docs)
    if prices:
        logger.info("prezzi €: min %.2f · mediana %.2f · max %.2f (n=%d)",
                    prices[0], st.median(prices), prices[-1], len(prices))
    close_db()
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", type=int, default=6)
    p.add_argument("--gain", type=float, default=None)
    p.add_argument("--seed", action="store_true")
    a = p.parse_args()
    sys.exit(asyncio.run(main(a.rounds, a.gain, a.seed)))
