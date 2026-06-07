"""Backfill STORICO prezzi sintetico in € (ravviva sparkline/grafici/var%).

Dopo il reset (D7) `price_history` è vuoto → serie piatte. Qui si genera, in modo
DETERMINISTICO e idempotente, uno storico plausibile che TERMINA sul prezzo corrente
(seed) di ogni atleta: random walk LIMITATO nella banda del motore, con mean-reversion
verso l'ancora e volatilità PER-ATLETA (alcuni titoli mossi, altri tranquilli).

Griglia temporale NON uniforme, allineata ai limiti del frontend (24h→24 punti,
7g→56, 30g→90): oraria nelle ultime 24h, ~4,5h fino a 7g, ~16h fino a 30g. Così
"ultimi N punti" coprono esattamente 24H / 7D / 30D con densità adeguata.

Garanzie:
- ultimo punto (ts≈now) = prezzo_corrente_eur ESATTO → prezzo attuale, var% e
  value=prezzo×1M restano coerenti; NON tocca prezzo/holdings/wallet/economia;
- rispetta il floor (10% del prezzo iniziale, in €) e il tetto (ancora×(1+cap));
- tocca SOLO `price_history` (cancella i propri reason="backfill" prima di riscrivere).

Uso (dalla cartella backend/):  python -m tools.backfill_price_history
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

from app.config.pricing_constants import DEVIAZIONE_CAP, FLOOR_PCT_PREZZO_INIZIALE
from app.core.db import close_db, get_db, init_db
from app.models.common import utc_now


def _u(key: str) -> float:
    """Uniforme deterministica [0,1) da una chiave (no stato RNG → idempotente)."""
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big") / 2**64


def _age_grid_hours() -> list[float]:
    """Età (ore fa) dei punti, dal più recente (0) al più vecchio (720h=30g).

    24 punti orari (0..23h) · +32 fino a 168h (7g) · +34 fino a 720h (30g) = 90.
    """
    ages = [float(h) for h in range(24)]                       # 0..23h (24)
    for j in range(1, 33):                                     # →168h (32)
        ages.append(24.0 + j * (168.0 - 24.0) / 32.0)
    for j in range(1, 35):                                     # →720h (34)
        ages.append(168.0 + j * (720.0 - 168.0) / 34.0)
    return ages                                               # len 90, asc per età


async def backfill_price_history(db) -> dict:
    now = utc_now()
    grid = _age_grid_hours()
    athletes = await db.athletes.find({"status": "ACTIVE"}).to_list(length=100_000)
    written = 0
    for a in athletes:
        aid = a["_id"]
        cur = float(a.get("prezzo_corrente_eur") or 0.0)
        ini = float(a.get("prezzo_iniziale_eur") or cur)
        equo = float(a.get("prezzo_equo_eur") or cur)
        if cur <= 0:
            continue
        floor = FLOOR_PCT_PREZZO_INIZIALE * ini
        tetto = equo * (1.0 + DEVIAZIONE_CAP)
        # volatilità per-atleta: ~0,15%/h (tranquillo) → ~1,3%/h (mosso)
        sigma_h = 0.0015 + _u(f"vol:{aid}") * 0.0115
        k_mr = 0.06  # mean-reversion verso l'ancora (per step)

        # pulizia: rigenera i propri punti + elimina punti FUORI BANDA (scala vecchia
        # pre-migrazione, es. snapshot/trade in Crediti) che falsano min/max e sparkline
        await db.price_history.delete_many({"athlete_id": aid, "reason": "backfill"})
        await db.price_history.delete_many({
            "athlete_id": aid,
            "$or": [{"prezzo": {"$lt": floor}}, {"prezzo": {"$gt": tetto}}],
        })

        # random walk ALL'INDIETRO dal presente: p[0]=cur, poi punti via via più vecchi
        prices = [cur]
        p = cur
        for i in range(1, len(grid)):
            dt_h = max(0.5, grid[i] - grid[i - 1])             # gap temporale del passo
            shock = (_u(f"bf:{aid}:{i}") - 0.5) * 2.0 * sigma_h * (dt_h ** 0.5)
            pull = k_mr * (equo - p) / equo                    # rientro verso l'ancora
            p = p * (1.0 + shock + pull)
            p = max(floor, min(tetto, p))
            prices.append(p)

        # scrivi: età decrescente → ts crescente; l'ultimo (now) = cur ESATTO
        points = []
        for i, age in enumerate(grid):
            prezzo = cur if age == 0.0 else round(prices[i], 6)
            points.append({
                "athlete_id": aid, "prezzo": prezzo,
                "deviazione": round(prezzo / equo - 1.0, 6) if equo else 0.0,
                "reason": "backfill", "ts": now - timedelta(hours=age),
            })
        if points:
            await db.price_history.insert_many(points)
            written += len(points)

    return {"athletes": len(athletes), "points": written, "per_athlete": len(grid)}


async def main() -> int:
    init_db()
    db = get_db()
    rep = await backfill_price_history(db)
    print(f"backfill price_history (€): {rep['athletes']} atleti · {rep['points']} punti "
          f"({rep['per_athlete']}/atleta, griglia 24H/7D/30D)")
    close_db()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
