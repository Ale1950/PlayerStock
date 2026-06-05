"""CLI: popola il DB con dati fittizi di Fase 3 (holdings + lots +
wallet_transactions + price_history) per validare gli endpoint Fase 4 E2E.

Uso (dalla cartella backend/):
    python -m app.cli.seed_phase3_mock --user-email user@playerstock.app

NB: idempotente sull'utente target. Pulisce e ricrea holdings/transazioni
per quell'utente. NON tocca le collezioni di altri utenti.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import logging
import sys

from app.core.db import close_db, get_db, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_phase3_mock")


async def _ensure_user(db, email: str) -> dict:
    """Crea o ritorna un user con saldo iniziale 10k."""
    user = await db.users.find_one({"email": email})
    if user:
        return user
    now = dt.datetime.now(dt.timezone.utc)
    doc = {
        "google_sub": f"mock-{email}", "email": email, "name": "Mario Rossi",
        "picture": None, "locale": "it", "country_iso2": "IT", "role": "user",
        "terms_accepted_at": now, "privacy_accepted_at": now,
        "created_at": now, "last_login_at": now, "status": "active",
    }
    res = await db.users.insert_one(doc)
    user = await db.users.find_one({"_id": res.inserted_id})
    return user


async def main(email: str) -> int:
    init_db()
    db = get_db()
    user = await _ensure_user(db, email)
    uid = user["_id"]
    now = dt.datetime.now(dt.timezone.utc)

    # Pulisce stato precedente dell'utente
    await db.holdings.delete_many({"user_id": uid})
    await db.wallet_transactions.delete_many({"user_id": uid})

    # 1. Wallet 10k crediti
    await db.user_wallets.update_one(
        {"user_id": uid},
        {"$set": {"balance_credits": 7_580.50, "updated_at": now}},
        upsert=True,
    )
    await db.wallet_transactions.insert_one({
        "user_id": uid, "type": "welcome_bonus", "amount": 10_000.0,
        "balance_after": 10_000.0, "description_it": "Bonus di benvenuto",
        "created_at": now - dt.timedelta(days=12),
    })

    # 2. Recupera 3 atleti di ruoli diversi
    atts = await db.athletes.find({"role": "ATT"}).limit(2).to_list(length=2)
    difs = await db.athletes.find({"role": "DIF"}).limit(1).to_list(length=1)
    pors = await db.athletes.find({"role": "POR"}).limit(1).to_list(length=1)
    sample = atts + difs + pors
    if len(sample) < 3:
        logger.error("Servono almeno 3 atleti nel DB. Esegui prima seed_roster.")
        close_db()
        return 1

    # 3. Posizioni:
    # - Atleta A (in utile): comprato a 0.0080, prezzo corrente alzato a 0.0125
    # - Atleta B (in perdita): comprato a 0.0100, ribassato a 0.0090
    # - Atleta C (multi-lot, profitto piccolo)
    # - Atleta D (POR, lotto vecchio breakeven)
    scenarios = [
        # (athlete, qty_lot1, price_lot1, days_ago1, qty_lot2, price_lot2, days_ago2, current_price)
        (sample[0], 5_000, 0.0080, 10, None,    None,    None, 0.0125),
        (sample[1], 3_000, 0.0100, 8,  None,    None,    None, 0.0090),
        (sample[2], 2_000, 0.0095, 9,  1_500,   0.0110,  3,    0.0115),
        (sample[3], 1_000, 0.0070, 15, None,    None,    None, 0.0070),  # breakeven
    ]
    bal = 10_000.0
    for athlete, q1, p1, d1, q2, p2, d2, cp in scenarios:
        lots = [{"qty": q1, "price": p1, "acquired_at": now - dt.timedelta(days=d1)}]
        total_qty = q1
        if q2 is not None:
            lots.append({"qty": q2, "price": p2, "acquired_at": now - dt.timedelta(days=d2)})
            total_qty += q2
        await db.holdings.insert_one({
            "user_id": uid, "athlete_id": athlete["_id"],
            "quantity": total_qty, "lots": lots,
            "created_at": lots[0]["acquired_at"], "updated_at": now,
        })
        # transazioni wallet
        for lot in lots:
            gross = lot["qty"] * lot["price"]
            fee = gross * 0.035
            bal -= gross + fee
            await db.wallet_transactions.insert_many([
                {"user_id": uid, "type": "trade_buy", "amount": -gross,
                 "balance_after": bal + fee,
                 "description_it": f"Acquisto {lot['qty']} quote",
                 "created_at": lot["acquired_at"]},
                {"user_id": uid, "type": "fee_buyer", "amount": -fee,
                 "balance_after": bal,
                 "description_it": "Commissione acquisto 3.5%",
                 "created_at": lot["acquired_at"]},
            ])

        # aggiorna prezzo corrente dell'atleta
        await db.athletes.update_one(
            {"_id": athlete["_id"]},
            {"$set": {"prezzo_corrente_crediti": cp, "updated_at": now}},
        )

        # popola price_history (30 punti, sinusoide simulata)
        await db.price_history.delete_many({"athlete_id": athlete["_id"]})
        history_points = []
        base = athlete.get("prezzo_iniziale_crediti", 0.01)
        for i in range(30):
            day = now - dt.timedelta(days=30 - i)
            # cresce verso il prezzo corrente con un po' di noise
            t = i / 29.0
            p = base + (cp - base) * t + (0.0003 * ((-1) ** i))
            p = max(p, 0.001)
            history_points.append({"athlete_id": athlete["_id"], "ts": day, "price": round(p, 6)})
        if history_points:
            await db.price_history.insert_many(history_points)

    # aggiorna saldo wallet con totale calcolato
    await db.user_wallets.update_one(
        {"user_id": uid},
        {"$set": {"balance_credits": round(bal, 4), "updated_at": now}},
    )

    logger.info(
        "✅ Seed Phase 3 mock OK | user=%s | uid=%s | balance=%.4f | positions=%d",
        email, uid, bal, len(scenarios),
    )
    close_db()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-email", default="user@playerstock.app")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.user_email)))
