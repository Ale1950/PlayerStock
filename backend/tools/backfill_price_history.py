"""Backfill storico prezzi con timestamp DISTRIBUITI (per le serie temporali).

`price_history` esistente ha ts ravvicinati (simulate_rounds usa utc_now() per tutti
i round) → le serie equity/prezzo collassano. Questo tool ricostruisce, in modo
DETERMINISTICO e INTERNO, ~30 punti giornalieri da prezzo_iniziale → prezzo_corrente
con piccolo rumore, ts spalmati sugli ultimi 30 giorni. reason="backfill".

NON tocca prezzo_corrente/holdings/wallet (solo ADDITIVO su price_history). Idempotente
(cancella i propri 'backfill' prima di riscrivere). Uso: python -m tools.backfill_price_history
"""
from __future__ import annotations

import asyncio
import hashlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from datetime import timedelta

from app.config.pricing_constants import FLOOR_PCT_PREZZO_INIZIALE
from app.core.db import close_db, get_db, init_db
from app.models.common import utc_now

DAYS = 30


def _u(key: str) -> float:
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big") / 2**64


async def main() -> int:
    init_db()
    db = get_db()
    now = utc_now()
    athletes = await db.athletes.find({"status": "ACTIVE"}).to_list(length=10_000)
    written = 0
    for a in athletes:
        aid = a["_id"]
        ini = float(a.get("prezzo_iniziale_eur", 0.01))
        cur = float(a.get("prezzo_corrente_eur", ini))
        floor = FLOOR_PCT_PREZZO_INIZIALE * ini
        await db.price_history.delete_many({"athlete_id": aid, "reason": "backfill"})
        points = []
        for d in range(DAYS, -1, -1):
            t = (DAYS - d) / DAYS  # 0→1
            base = ini + (cur - ini) * t
            noise = (_u(f"bf:{aid}:{d}") - 0.5) * 0.06 * base  # ±3%
            p = max(floor, base + noise)
            if d == 0:
                p = cur  # l'ultimo punto = prezzo corrente reale
            points.append({"athlete_id": aid, "prezzo": round(p, 8),
                           "reason": "backfill", "ts": now - timedelta(days=d)})
        if points:
            await db.price_history.insert_many(points)
            written += len(points)
    print(f"backfill: {len(athletes)} atleti · {written} punti price_history (ts su {DAYS} giorni)")
    close_db()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
