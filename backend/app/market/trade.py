"""Esecuzione ordini di mercato contro la CASA (pool a due lati).

MVP: nessun matching P2P. La casa è sempre controparte al prezzo di quotazione
corrente; buy ×(1+fee), sell ×(1−fee). Le fee confluiscono in `house_account`
(sink economia). Scarsità preservata: float = primary_pool_qty + circulating_qty.

NOTA atomicità: in MVP le scritture sono sequenziali (mongomock non supporta
transazioni). In produzione su Atlas (replica set) avvolgere in una transazione
multi-documento. Le validazioni avvengono PRIMA di qualunque scrittura.
"""
from __future__ import annotations

from datetime import datetime

from app.core.errors import err_bad_request, err_not_found
from app.market.rules import (
    assert_within_cap,
    buy_cost,
    buy_gross,
    consume_lots_fifo,
    fee_buyer,
    fee_seller,
    sell_gross,
    sell_proceeds,
    sellable_quantity,
)
from app.models.common import utc_now


async def _load_active_athlete(db, athlete_id) -> dict:
    a = await db.athletes.find_one({"_id": athlete_id, "status": "ACTIVE"})
    if not a:
        raise err_not_found("athlete.not_found", "Atleta non trovato o non attivo")
    return a


async def _credit_house(db, amount: float, now: datetime) -> None:
    await db.house_account.update_one(
        {"_id": "house"},
        {"$inc": {"fees_collected": amount}, "$set": {"updated_at": now}},
        upsert=True,
    )


async def execute_buy(db, *, user_id, athlete_id, qty: int, now: datetime | None = None) -> dict:
    now = now or utc_now()
    if qty <= 0:
        raise err_bad_request("market.invalid_qty", "Quantità non valida")

    athlete = await _load_active_athlete(db, athlete_id)
    price = athlete["prezzo_corrente_crediti"]
    pool = athlete.get("primary_pool_qty", 0)
    if qty > pool:
        raise err_bad_request(
            "market.pool_insufficient",
            "Quote insufficienti nel pool (sold out)",
            extra={"available": pool, "requested": qty},
        )

    holding = await db.holdings.find_one({"user_id": user_id, "athlete_id": athlete_id})
    current_qty = holding["quantity"] if holding else 0
    assert_within_cap(current_qty=current_qty, add_qty=qty)

    wallet = await db.user_wallets.find_one({"user_id": user_id})
    balance = wallet["balance_credits"] if wallet else 0.0
    gross = buy_gross(qty, price)
    fee = fee_buyer(qty, price)
    cost = buy_cost(qty, price)
    if balance < cost:
        raise err_bad_request(
            "market.insufficient_funds",
            "Saldo Crediti insufficiente",
            extra={"balance": balance, "cost": cost},
        )

    # ── scritture (validazioni superate) ──
    after_gross = balance - gross
    after_fee = after_gross - fee
    await db.user_wallets.update_one(
        {"user_id": user_id},
        {"$set": {"balance_credits": after_fee, "updated_at": now}},
    )
    await db.athletes.update_one(
        {"_id": athlete_id},
        {"$inc": {"primary_pool_qty": -qty, "circulating_qty": qty}, "$set": {"updated_at": now}},
    )
    await db.holdings.update_one(
        {"user_id": user_id, "athlete_id": athlete_id},
        {
            "$inc": {"quantity": qty},
            "$push": {"lots": {"qty": qty, "acquired_at": now, "price": price}},
            "$set": {"updated_at": now},
            "$setOnInsert": {"user_id": user_id, "athlete_id": athlete_id, "created_at": now},
        },
        upsert=True,
    )
    await db.wallet_transactions.insert_many([
        {"user_id": user_id, "type": "trade_buy", "amount": -gross, "balance_after": after_gross,
         "description_it": f"Acquisto {qty} quote", "created_at": now},
        {"user_id": user_id, "type": "fee_buyer", "amount": -fee, "balance_after": after_fee,
         "description_it": "Commissione acquisto 3.5%", "created_at": now},
    ])
    await db.orders.insert_one({
        "user_id": user_id, "athlete_id": athlete_id, "side": "buy", "type": "market",
        "qty": qty, "qty_filled": qty, "price": price, "fee": fee,
        "status": "filled", "created_at": now,
    })
    await db.trades.insert_one({
        "athlete_id": athlete_id, "buyer_id": user_id, "seller_id": "HOUSE",
        "qty": qty, "price": price, "fee_buyer": fee, "fee_seller": 0.0, "ts": now,
    })
    await _credit_house(db, fee, now)

    return {"side": "buy", "qty": qty, "price": price, "gross": gross, "fee": fee,
            "cost": cost, "new_balance": after_fee}


async def execute_sell(db, *, user_id, athlete_id, qty: int, now: datetime | None = None) -> dict:
    now = now or utc_now()
    if qty <= 0:
        raise err_bad_request("market.invalid_qty", "Quantità non valida")

    athlete = await _load_active_athlete(db, athlete_id)
    price = athlete["prezzo_corrente_crediti"]

    holding = await db.holdings.find_one({"user_id": user_id, "athlete_id": athlete_id})
    if not holding or holding["quantity"] < qty:
        raise err_bad_request("market.not_enough_shares", "Non possiedi abbastanza quote")

    sellable = sellable_quantity(holding["lots"], now)
    if qty > sellable:
        raise err_bad_request(
            "market.holding_locked",
            "Quote ancora in holding minimo (7 giorni)",
            extra={"sellable": sellable, "requested": qty},
        )

    gross = sell_gross(qty, price)
    fee = fee_seller(qty, price)
    proceeds = sell_proceeds(qty, price)

    # ── scritture ──
    new_lots = consume_lots_fifo(holding["lots"], qty)
    await db.holdings.update_one(
        {"user_id": user_id, "athlete_id": athlete_id},
        {"$set": {"lots": new_lots, "quantity": holding["quantity"] - qty, "updated_at": now}},
    )
    await db.athletes.update_one(
        {"_id": athlete_id},
        {"$inc": {"primary_pool_qty": qty, "circulating_qty": -qty}, "$set": {"updated_at": now}},
    )
    wallet = await db.user_wallets.find_one({"user_id": user_id})
    balance = wallet["balance_credits"] if wallet else 0.0
    after_gross = balance + gross
    after_fee = after_gross - fee
    await db.user_wallets.update_one(
        {"user_id": user_id},
        {"$set": {"balance_credits": after_fee, "updated_at": now}},
    )
    await db.wallet_transactions.insert_many([
        {"user_id": user_id, "type": "trade_sell", "amount": gross, "balance_after": after_gross,
         "description_it": f"Vendita {qty} quote", "created_at": now},
        {"user_id": user_id, "type": "fee_seller", "amount": -fee, "balance_after": after_fee,
         "description_it": "Commissione vendita 3.5%", "created_at": now},
    ])
    await db.orders.insert_one({
        "user_id": user_id, "athlete_id": athlete_id, "side": "sell", "type": "market",
        "qty": qty, "qty_filled": qty, "price": price, "fee": fee,
        "status": "filled", "created_at": now,
    })
    await db.trades.insert_one({
        "athlete_id": athlete_id, "buyer_id": "HOUSE", "seller_id": user_id,
        "qty": qty, "price": price, "fee_buyer": 0.0, "fee_seller": fee, "ts": now,
    })
    await _credit_house(db, fee, now)

    return {"side": "sell", "qty": qty, "price": price, "gross": gross, "fee": fee,
            "proceeds": proceeds, "new_balance": after_fee}
