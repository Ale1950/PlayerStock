"""Smoke read-only Fase 4 su Atlas (JWT mintato, no login Google).

Verifica che /portfolio /wallet /leaderboard /athletes/{id}/price-history
diano dati sensati sul DB reale. NON scrive nulla (a parte garantire un utente
di test con almeno una posizione, se assente).
"""
import asyncio

import httpx
from bson import ObjectId

from app.core.db import close_db, get_db, init_db
from app.core.security import create_access_token
from app.models.common import utc_now

API = "http://127.0.0.1:8001/api"
EMAIL = "smoke-fase3@test.local"  # riusa l'utente del precedente smoke (ha holdings)


def ok(cond, msg):
    print(("  [OK] " if cond else "  [FAIL] ") + msg)
    if not cond:
        raise SystemExit("SMOKE FALLITO: " + msg)


async def _ensure_user_with_position(db):
    user = await db.users.find_one({"email": EMAIL})
    if user:
        h = await db.holdings.find_one({"user_id": user["_id"], "quantity": {"$gt": 0}})
        if h:
            return user["_id"], h["athlete_id"]
    # crea utente + wallet + 1 posizione (lotto sotto prezzo -> P&L positivo atteso)
    uid = user["_id"] if user else ObjectId()
    now = utc_now()
    if not user:
        await db.users.insert_one({
            "_id": uid, "google_sub": "smoke-f4", "email": EMAIL, "name": "Smoke F4",
            "status": "active", "role": "user", "locale": "it", "created_at": now,
        })
    await db.user_wallets.update_one(
        {"user_id": uid}, {"$set": {"balance_credits": 100.0, "updated_at": now}}, upsert=True
    )
    a = await db.athletes.find_one({"sport_id": "calcio", "status": "ACTIVE"})
    await db.holdings.update_one(
        {"user_id": uid, "athlete_id": a["_id"]},
        {"$set": {"quantity": 50, "lots": [{"qty": 50, "price": a["prezzo_corrente_crediti"] * 0.8,
                                            "acquired_at": now}], "updated_at": now},
         "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    return uid, a["_id"]


async def main():
    init_db()
    db = get_db()
    uid, aid = await _ensure_user_with_position(db)
    token = create_access_token(user_id=str(uid))
    H = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30) as c:
        # ── PORTFOLIO ──
        p = (await c.get(f"{API}/portfolio", headers=H)).json()
        ok("totals" in p and "positions" in p, "portfolio: struttura totals+positions")
        ok(len(p["positions"]) >= 1, f"portfolio: {len(p['positions'])} posizioni")
        pos = p["positions"][0]
        ok(pos.get("team_fantasy_name"), f"portfolio: team fantasy presente ({pos.get('team_fantasy_name')})")
        ok("internal_full_name" not in str(p), "portfolio: nessun internal_full_name (L2)")
        t = p["totals"]
        ok(abs(t["total_equity"] - (t["cash_credits"] + t["positions_value"])) < 1e-6,
           "portfolio: total_equity = cash + titoli")
        print(f"    equity={t['total_equity']:.4f} cash={t['cash_credits']:.4f} "
              f"titoli={t['positions_value']:.4f} P&L={t['total_pnl_abs']:.4f}")

        # ── WALLET ──
        w = (await c.get(f"{API}/wallet", headers=H)).json()
        ok("balance_credits" in w and "recent_transactions" in w, "wallet: saldo + transazioni")
        print(f"    saldo={w['balance_credits']:.4f} tx={len(w['recent_transactions'])}")

        # ── LEADERBOARD ──
        lb = (await c.get(f"{API}/leaderboard", headers=H)).json()
        ok("items" in lb and "total_users" in lb, "leaderboard: items + total_users")
        ok(any(it.get("is_self") for it in lb["items"]) or lb.get("self") is not None,
           "leaderboard: self presente")
        ok("email" not in str(lb), "leaderboard: nessuna email esposta")
        print(f"    trader={lb['total_users']} top={lb['items'][0]['display_name'] if lb['items'] else '-'}")

        # ── PRICE HISTORY (sparkline, pubblico) ──
        ph = (await c.get(f"{API}/athletes/{aid}/price-history?limit=30")).json()
        ok(ph["count"] >= 1, f"price-history: {ph['count']} punti")
        ok(all("price" in pt and "ts" in pt for pt in ph["points"]), "price-history: punti {ts,price}")
        print(f"    punti={ph['count']}")

    print("\nSMOKE FASE 4 (read-only): VERDE")
    close_db()


if __name__ == "__main__":
    asyncio.run(main())
