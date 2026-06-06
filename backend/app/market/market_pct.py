"""Mercato%: pressione domanda/offerta da net order flow → bucket → driver.

net_qty = quote comprate − quote vendute nella finestra (per atleta).
Bucket per |net|: 1-5 / 6-20 / >20 → MARKET_DRIVERS (±1.2 / ±2.0 / ±2.5 %).
"""
from __future__ import annotations

from datetime import datetime

from app.config.pricing_constants import MARKET_DRIVERS
from app.pricing.engine import apply_tick
from app.models.common import utc_now


def _bucket(n: int) -> str:
    if n <= 5:
        return "1_5"
    if n <= 20:
        return "6_20"
    return "over_20"


def market_pct_from_net(net_qty: int) -> float:
    """Variazione % di mercato data la pressione netta (segno = direzione)."""
    if net_qty == 0:
        return 0.0
    bucket = _bucket(abs(net_qty))
    side = "buy" if net_qty > 0 else "sell"
    return MARKET_DRIVERS[f"{side}_{bucket}"]


async def apply_market_flow(
    db, *, since: datetime, until: datetime | None = None, now: datetime | None = None
) -> dict:
    """Consolida il net order flow della finestra → mercato% → tick di prezzo.

    Aggrega gli ordini (buy/sell) per atleta nell'intervallo [since, until], calcola
    la pressione netta, applica `apply_tick` (perf%=0) con clamp+floor e registra in
    `price_history` (reason="market").
    """
    now = now or utc_now()
    match: dict = {"created_at": {"$gte": since}}
    if until is not None:
        match["created_at"]["$lte"] = until

    orders = await db.orders.find(match).to_list(length=100_000)
    net_by_athlete: dict = {}
    for o in orders:
        sign = 1 if o["side"] == "buy" else -1
        net_by_athlete[o["athlete_id"]] = net_by_athlete.get(o["athlete_id"], 0) + sign * o["qty"]

    moved = 0
    for athlete_id, net in net_by_athlete.items():
        pct = market_pct_from_net(net)
        if pct == 0.0:
            continue
        a = await db.athletes.find_one({"_id": athlete_id})
        if not a:
            continue
        res = apply_tick(
            prezzo_corrente=a["prezzo_corrente_eur"],
            prezzo_iniziale=a["prezzo_iniziale_eur"],
            perf_pct=0.0,
            mercato_pct=pct,
        )
        await db.athletes.update_one(
            {"_id": athlete_id},
            {"$set": {"prezzo_corrente_eur": res.new_price, "updated_at": now}},
        )
        await db.price_history.insert_one({
            "athlete_id": athlete_id, "prezzo": res.new_price, "mercato_pct": pct,
            "net_flow": net, "reason": "market", "floored": res.floored, "ts": now,
        })
        moved += 1

    return {"athletes_moved": moved, "orders_considered": len(orders)}
