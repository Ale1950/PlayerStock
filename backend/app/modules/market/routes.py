"""Market module (Fase 3): buy/sell vs casa, holdings, quote.

MVP semplificato: nessun order book P2P. Prezzo = quotazione (formula); gli
scambi avvengono al prezzo corrente; il net flow muove la quotazione (mercato%).
"""
from __future__ import annotations

from typing import Annotated, Literal

from bson import ObjectId
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.core.deps import CurrentUserDep, DBDep
from app.core.errors import err_not_found
from app.market.rules import buy_cost, fee_buyer, fee_seller, sell_proceeds
from app.market.trade import execute_buy, execute_sell

router = APIRouter(tags=["market"])


class OrderRequest(BaseModel):
    athlete_id: str
    side: Literal["buy", "sell"]
    qty: int = Field(..., gt=0)


def _oid(value: str, code: str, msg: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception:
        raise err_not_found(code, msg)


@router.post("/market/orders")
async def place_order(req: OrderRequest, user: CurrentUserDep, db: DBDep) -> dict:
    aid = _oid(req.athlete_id, "athlete.invalid_id", "ID atleta non valido")
    if req.side == "buy":
        return await execute_buy(db, user_id=user["_id"], athlete_id=aid, qty=req.qty)
    return await execute_sell(db, user_id=user["_id"], athlete_id=aid, qty=req.qty)


@router.get("/market/orders")
async def my_orders(
    user: CurrentUserDep,
    db: DBDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    flt = {"user_id": user["_id"]}
    total = await db.orders.count_documents(flt)
    skip = (page - 1) * page_size
    cursor = db.orders.find(flt).sort("created_at", -1).skip(skip).limit(page_size)
    items = []
    for o in await cursor.to_list(length=page_size):
        o["id"] = str(o.pop("_id"))
        o["athlete_id"] = str(o["athlete_id"])
        o["user_id"] = str(o["user_id"])
        items.append(o)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/market/holdings")
async def my_holdings(user: CurrentUserDep, db: DBDep) -> list[dict]:
    holdings = await db.holdings.find(
        {"user_id": user["_id"], "quantity": {"$gt": 0}}
    ).to_list(length=1000)
    out: list[dict] = []
    for h in holdings:
        a = await db.athletes.find_one({"_id": h["athlete_id"]})
        if not a:
            continue
        price = a["prezzo_corrente_eur"]
        out.append({
            "athlete_id": str(h["athlete_id"]),
            "display_label": a.get("display_label"),
            "role": a.get("role"),
            "quantity": h["quantity"],
            "prezzo_corrente_eur": price,
            "valore_corrente_eur": h["quantity"] * price,
        })
    return out


@router.get("/market/athletes/{athlete_id}/quote")
async def quote(
    athlete_id: str, db: DBDep, qty: Annotated[int, Query(gt=0)] = 1
) -> dict:
    aid = _oid(athlete_id, "athlete.invalid_id", "ID atleta non valido")
    a = await db.athletes.find_one({"_id": aid, "status": "ACTIVE"})
    if not a:
        raise err_not_found("athlete.not_found", "Atleta non trovato")
    price = a["prezzo_corrente_eur"]
    return {
        "athlete_id": athlete_id,
        "prezzo_corrente_eur": price,
        "primary_pool_qty": a.get("primary_pool_qty", 0),
        "qty": qty,
        "buy_cost": buy_cost(qty, price),
        "buy_fee": fee_buyer(qty, price),
        "sell_proceeds": sell_proceeds(qty, price),
        "sell_fee": fee_seller(qty, price),
    }
