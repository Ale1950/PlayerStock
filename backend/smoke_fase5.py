"""Smoke live Fase 5 su Atlas (JWT mintato): reward provider/balance/wallet/heartbeat.

NB: il saldo è PLACEHOLDER (is_placeholder=True), non NACKL reale.
"""
import asyncio
import hashlib
import hmac
import time

import httpx
from bson import ObjectId

from app.config.settings import get_settings
from app.core.db import close_db, get_db, init_db
from app.core.security import create_access_token
from app.models.common import utc_now

API = "http://127.0.0.1:8001/api"
EMAIL = "smoke-fase3@test.local"  # ha ordini reali -> attività osservata


def ok(cond, msg):
    print(("  [OK] " if cond else "  [FAIL] ") + msg)
    if not cond:
        raise SystemExit("SMOKE FALLITO: " + msg)


async def main():
    init_db()
    db = get_db()
    s = get_settings()

    user = await db.users.find_one({"email": EMAIL})
    if not user:
        uid = ObjectId()
        await db.users.insert_one({"_id": uid, "google_sub": "smoke-f5", "email": EMAIL,
                                   "name": "Smoke F5", "status": "active", "role": "user",
                                   "locale": "it", "created_at": utc_now()})
    else:
        uid = user["_id"]
    # reset stato per evitare rate-limit da run precedenti
    await db.reward_state.delete_many({"user_id": uid})

    token = create_access_token(user_id=str(uid))
    H = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30) as c:
        prov = (await c.get(f"{API}/reward/provider", headers=H)).json()
        ok(prov["is_placeholder"] is True, f"provider placeholder ({prov['provider_name']})")
        ok(prov["mining_status"] == "coming_soon", "mining_status=coming_soon")

        bal0 = (await c.get(f"{API}/reward/balance", headers=H)).json()
        ok(bal0["currency"] == "NACKL" and bal0["is_placeholder"] is True, "balance NACKL placeholder")
        print(f"    saldo iniziale={bal0['amount']}")

        # wallet: rifiuta seed
        seed = "legal winner thank year wave sausage worth useful legal winner thank yellow"
        r = await c.post(f"{API}/reward/wallet/connect", headers=H, json={"mining_public_key": seed})
        ok(r.status_code == 400 and r.json()["detail"]["error_code"] == "reward.wallet.seed_not_allowed",
           "wallet connect RIFIUTA seed phrase")

        # wallet: accetta public key
        r = await c.post(f"{API}/reward/wallet/connect", headers=H, json={"mining_public_key": "0x" + "a" * 64})
        ok(r.status_code == 200 and r.json()["connected"], "wallet connect accetta public key")
        ok((await c.get(f"{API}/reward/provider", headers=H)).json()["wallet_connected"] is True,
           "provider: wallet_connected=true")

        # heartbeat firmato
        nonce = f"smoke-{int(time.time())}"
        ts = int(time.time())
        msg = f"{uid}:{nonce}:{ts}"
        sig = hmac.new(s.REWARD_HEARTBEAT_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
        r = await c.post(f"{API}/reward/heartbeat", headers=H,
                         json={"nonce": nonce, "ts": ts, "signature": sig})
        ok(r.status_code == 200, f"heartbeat 200 ({r.status_code} {r.text[:120]})")
        hb = r.json()
        ok(hb["accrued"] >= 0.1, f"heartbeat accredita placeholder (accrued={hb['accrued']}, activity={hb['activity_count']})")
        ok(hb["balance"]["is_placeholder"] is True, "saldo post-heartbeat placeholder")

        # heartbeat replay -> 409
        r2 = await c.post(f"{API}/reward/heartbeat", headers=H,
                          json={"nonce": nonce, "ts": ts, "signature": sig})
        ok(r2.status_code in (409, 429), f"heartbeat replay/rate-limit bloccato ({r2.status_code})")

    print("\nSMOKE FASE 5: VERDE")
    close_db()


if __name__ == "__main__":
    asyncio.run(main())
