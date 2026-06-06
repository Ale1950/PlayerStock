"""CLI: ancora di mercato in € — `market_value_eur_seed` + prezzo quota (= seed/FLOAT).

Migrazione € (D7): il valore €M (Opzione B, coda pesante €0,50–€115M) è l'UNICA
fonte di verità. Prezzo quota = market_value_eur_seed / FLOAT → ancora del motore
ibrido (deviazione/floor/mean-reversion restano in %). value mostrato = prezzo × FLOAT.

Setta, per atleta (deterministico, per squadra): `market_value_eur_seed`,
`prezzo_iniziale_eur`, `prezzo_equo_eur`, `prezzo_corrente_eur`, `valore_iniziale_eur`.
Azzera la deviazione (ancora pulita). Idempotente. NON tocca holdings/ledger/NACKL.

Uso (dalla cartella backend/):
    python -m app.cli.backfill_market_value
"""
from __future__ import annotations

import asyncio
import logging

from app.core.db import close_db, get_db, init_db
from app.models.common import utc_now
from app.valuation.market_value import assign_team_market_values, price_from_market_value

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill_mv")


async def backfill_market_values(db) -> int:
    """Assegna valore €M (seed) + prezzo quota €, per squadra. Ritorna il conteggio."""
    athletes = await db.athletes.find({}).to_list(length=100_000)
    by_team: dict = {}
    for a in athletes:
        by_team.setdefault(a.get("team_fantasy_id"), []).append(a)

    now = utc_now()
    count = 0
    for players in by_team.values():
        rows = [{
            "key": str(p["_id"]),
            "score": float(p.get("score_performance", 1.0)),
            "fattore_squadra": float(p.get("fattore_squadra", 1.0)),
        } for p in players]
        values = assign_team_market_values(rows)
        for p in players:
            seed = values[str(p["_id"])]
            prezzo = price_from_market_value(seed, int(p.get("float_quote") or 1_000_000))
            await db.athletes.update_one(
                {"_id": p["_id"]},
                {"$set": {
                    "market_value_eur_seed": seed,
                    "valore_iniziale_eur": seed,
                    "prezzo_iniziale_eur": prezzo,
                    "prezzo_equo_eur": prezzo,
                    "prezzo_corrente_eur": prezzo,
                    "deviazione": 0.0, "deviazione_ts": now,
                    "updated_at": now,
                }},
            )
            count += 1
    return count


async def main() -> int:
    init_db()
    db = get_db()
    n = await backfill_market_values(db)
    logger.info("Ancora € di mercato: %d atleti aggiornati", n)
    close_db()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
