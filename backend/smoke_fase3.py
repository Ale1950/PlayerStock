"""Smoke live Fase 3 su Atlas (no login Google: JWT firmato a mano).

Verifica: buy/sell via endpoint (JWT), market% (net flow->tick->floor), atomicità
(errore a metà trade -> rollback). NON ri-seeda (i pool restano quelli reali).
"""
import asyncio
from datetime import timedelta

import httpx
from bson import ObjectId

from app.core.db import close_db, get_db, init_db
from app.core.security import create_access_token
from app.market.market_pct import apply_market_flow
from app.market import trade as trade_mod
from app.models.common import utc_now

API = "http://127.0.0.1:8001/api"
EMAIL = "smoke-fase3@test.local"


def ok(cond, msg):
    print(("  [OK] " if cond else "  [FAIL] ") + msg)
    if not cond:
        raise SystemExit("SMOKE FAILED: " + msg)


async def main():
    init_db()
    db = get_db()

    # ── pulizia test user precedente ──
    old = await db.users.find_one({"email": EMAIL})
    if old:
        uid_old = old["_id"]
        await db.holdings.delete_many({"user_id": uid_old})
        await db.orders.delete_many({"user_id": uid_old})
        await db.user_wallets.delete_many({"user_id": uid_old})
        await db.users.delete_one({"_id": uid_old})

    uid = ObjectId()
    now = utc_now()
    await db.users.insert_one({
        "_id": uid, "google_sub": "smoke-fase3-sub", "email": EMAIL, "name": "Smoke F3",
        "status": "active", "role": "user", "locale": "it", "created_at": now,
    })
    await db.user_wallets.insert_one({"user_id": uid, "balance_credits": 50.0, "updated_at": now})

    athlete = await db.athletes.find_one({"sport_id": "calcio", "status": "ACTIVE"})
    aid = athlete["_id"]
    price0 = athlete["prezzo_corrente_crediti"]
    pool0 = athlete["primary_pool_qty"]
    circ0 = athlete["circulating_qty"]
    house0 = (await db.house_account.find_one({"_id": "house"}) or {}).get("fees_collected", 0.0)
    print(f"Atleta {athlete['display_label']} prezzo={price0:.5f} pool={pool0} circ={circ0}")

    token = create_access_token(user_id=str(uid))
    H = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30) as c:
        # ── QUOTE ──
        q = (await c.get(f"{API}/market/athletes/{aid}/quote?qty=100", headers=H)).json()
        print("QUOTE:", q)

        # ── BUY 100 ──
        r = await c.post(f"{API}/market/orders", headers=H,
                         json={"athlete_id": str(aid), "side": "buy", "qty": 100})
        ok(r.status_code == 200, f"buy 200 ({r.status_code} {r.text[:120]})")
        buy = r.json()

        w = await db.user_wallets.find_one({"user_id": uid})
        a1 = await db.athletes.find_one({"_id": aid})
        h1 = await db.holdings.find_one({"user_id": uid, "athlete_id": aid})
        house1 = (await db.house_account.find_one({"_id": "house"}))["fees_collected"]
        ok(abs(w["balance_credits"] - (50.0 - 100 * price0 * 1.035)) < 1e-9, "wallet scalato di costo+fee")
        ok(a1["primary_pool_qty"] == pool0 - 100, "pool -100")
        ok(a1["circulating_qty"] == circ0 + 100, "circolante +100")
        ok(h1["quantity"] == 100, "holding = 100")
        ok(abs(house1 - house0 - 100 * price0 * 0.035) < 1e-9, "fee buyer -> house")

        # ── SELL: pre-data il lotto a 8gg fa per superare holding 7gg ──
        await db.holdings.update_one(
            {"_id": h1["_id"]},
            {"$set": {"lots.0.acquired_at": now - timedelta(days=8)}},
        )
        r = await c.post(f"{API}/market/orders", headers=H,
                         json={"athlete_id": str(aid), "side": "sell", "qty": 40})
        ok(r.status_code == 200, f"sell 200 ({r.status_code} {r.text[:120]})")

        w2 = await db.user_wallets.find_one({"user_id": uid})
        a2 = await db.athletes.find_one({"_id": aid})
        h2 = await db.holdings.find_one({"user_id": uid, "athlete_id": aid})
        ok(w2["balance_credits"] > w["balance_credits"], "wallet aumentato (proceeds)")
        ok(a2["primary_pool_qty"] == pool0 - 60, "pool tornato a -60 netto")
        ok(a2["circulating_qty"] == circ0 + 60, "circolante +60 netto")
        ok(h2["quantity"] == 60, "holding = 60")

    # ── MARKET%: net flow finestra -> tick ──
    price_before_flow = (await db.athletes.find_one({"_id": aid}))["prezzo_corrente_crediti"]
    flow = await apply_market_flow(db, since=now - timedelta(minutes=5))
    a3 = await db.athletes.find_one({"_id": aid})
    floor = 0.10 * a3["prezzo_iniziale_crediti"]
    ok(flow["athletes_moved"] >= 1, f"market flow ha mosso {flow['athletes_moved']} atleti")
    ok(a3["prezzo_corrente_crediti"] != price_before_flow, "prezzo mosso dal net flow")
    ok(a3["prezzo_corrente_crediti"] >= floor - 1e-12, "prezzo >= floor 10%")
    print(f"  net flow -> prezzo {price_before_flow:.5f} -> {a3['prezzo_corrente_crediti']:.5f}")

    # ── ATOMICITÀ: errore a metà trade -> rollback (transazione Atlas) ──
    wallet_before = (await db.user_wallets.find_one({"user_id": uid}))["balance_credits"]
    pool_before = (await db.athletes.find_one({"_id": aid}))["primary_pool_qty"]
    orig = trade_mod._credit_house

    async def boom(*a, **k):
        raise RuntimeError("errore iniettato a metà trade")

    trade_mod._credit_house = boom
    raised = False
    try:
        await trade_mod.execute_buy(db, user_id=uid, athlete_id=aid, qty=10)
    except RuntimeError:
        raised = True
    finally:
        trade_mod._credit_house = orig

    wallet_after = (await db.user_wallets.find_one({"user_id": uid}))["balance_credits"]
    pool_after = (await db.athletes.find_one({"_id": aid}))["primary_pool_qty"]
    ok(raised, "errore propagato")
    ok(abs(wallet_after - wallet_before) < 1e-12, "ROLLBACK: wallet invariato")
    ok(pool_after == pool_before, "ROLLBACK: pool invariato")

    print("\nSMOKE FASE 3: VERDE")
    close_db()


if __name__ == "__main__":
    asyncio.run(main())
