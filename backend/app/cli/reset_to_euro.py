"""CLI: RESET pulito alla scala € (migrazione D7, pre-lancio).

Niente conversioni: tutti ripartono da zero in €.
  • atleti  → ancora € (= market_value_eur_seed / FLOAT), deviazione azzerata,
              pool IPO ripristinato (primary_pool_qty = float, circulating_qty = 0);
  • wallet  → €1.000.000 per ogni utente, ledger transazioni azzerato + welcome bonus;
  • mercato → holdings / orders / trades / price_history / house_account azzerati;
  • engagement crediti → stato/cap giornaliero azzerati.

NON tocca il NACKL (ledger `nackl_ledger` / `reward_balances`): separato e invariato.

Uso (dalla cartella backend/):
    python -m app.cli.reset_to_euro            # esegue
    python -m app.cli.reset_to_euro --dry      # mostra solo cosa farebbe
"""
from __future__ import annotations

import asyncio
import logging
import sys

from app.cli.backfill_market_value import backfill_market_values
from app.config.pricing_constants import (
    BUDGET_INIZIALE_UTENTE_EUR,
    FLOAT_AZIONI_PER_GIOCATORE,
)
from app.core.db import close_db, get_db, init_db
from app.models.common import utc_now

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reset_eur")

# Collezioni di trading/economia da AZZERARE (NON include nulla del NACKL).
TRADING_COLLECTIONS = [
    "holdings", "orders", "trades", "price_history", "house_account",
    "wallet_transactions", "engagement_credit_grants", "engagement_credit_state",
]


async def reset_to_euro(db, *, dry_run: bool = False) -> dict:
    now = utc_now()
    report: dict = {}

    # 1. Atleti → ancora € + pool IPO + deviazione azzerata
    n_ath = await db.athletes.count_documents({})
    report["athletes"] = n_ath
    if not dry_run:
        await db.athletes.update_many({}, {"$set": {
            "primary_pool_qty": FLOAT_AZIONI_PER_GIOCATORE, "circulating_qty": 0,
            "deviazione": 0.0, "deviazione_ts": now, "updated_at": now,
        }})
        await backfill_market_values(db)  # market_value_eur_seed + prezzo €

    # 2. Azzera trading/economia (NON NACKL)
    for col in TRADING_COLLECTIONS:
        report[col] = await db[col].count_documents({})
        if not dry_run:
            await db[col].delete_many({})

    # 3. Wallet → €1.000.000 per ogni utente + welcome bonus
    users = await db.users.find({}, {"_id": 1}).to_list(length=1_000_000)
    report["users"] = len(users)
    if not dry_run:
        await db.user_wallets.delete_many({})
        for u in users:
            uid = u["_id"]
            await db.user_wallets.insert_one({
                "user_id": uid, "balance_eur": BUDGET_INIZIALE_UTENTE_EUR, "updated_at": now,
            })
            await db.wallet_transactions.insert_one({
                "user_id": uid, "type": "welcome_bonus", "amount": BUDGET_INIZIALE_UTENTE_EUR,
                "balance_after": BUDGET_INIZIALE_UTENTE_EUR,
                "description_it": "Fondo iniziale €1.000.000", "created_at": now,
            })

    # 4. NACKL: lasciato INTATTO (nessuna operazione)
    report["nackl"] = "INTATTO (non toccato)"
    return report


async def main(dry_run: bool = False) -> int:
    init_db()
    db = get_db()
    rep = await reset_to_euro(db, dry_run=dry_run)
    logger.info("%s reset €: %s", "ANTEPRIMA" if dry_run else "FATTO", rep)
    close_db()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(dry_run="--dry" in sys.argv)))
