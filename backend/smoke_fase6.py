"""Smoke live Fase 6 (engagement) su Atlas (JWT mintato).

Verifica streak/quiz/predictions + invariante sicurezza: /quizzes NON espone correct_index.
NB: reward via stub RewardClient (is_placeholder=True), NON NACKL reale.
"""
import asyncio

import httpx
from bson import ObjectId

from app.core.db import close_db, get_db, init_db
from app.core.security import create_access_token
from app.models.common import utc_now

API = "http://127.0.0.1:8001/api"
EMAIL = "smoke-fase3@test.local"


def ok(cond, msg):
    print(("  [OK] " if cond else "  [FAIL] ") + msg)
    if not cond:
        raise SystemExit("SMOKE FALLITO: " + msg)


async def main():
    init_db()
    db = get_db()

    user = await db.users.find_one({"email": EMAIL})
    if not user:
        uid = ObjectId()
        await db.users.insert_one({"_id": uid, "google_sub": "smoke-f6", "email": EMAIL,
                                   "name": "Smoke F6", "status": "active", "role": "user",
                                   "locale": "it", "created_at": utc_now()})
    else:
        uid = user["_id"]

    # reset stato engagement del test-user per idempotenza
    await db.login_streaks.delete_many({"user_id": uid})
    await db.quiz_attempts.delete_many({"user_id": uid})
    await db.predictions.delete_many({"user_id": uid})

    # seed 1 quiz di prova (con correct_index, che NON deve trapelare)
    await db.quizzes.delete_many({"title": "SMOKE Quiz"})
    quiz = await db.quizzes.insert_one({
        "title": "SMOKE Quiz", "description": "Test", "active": True, "created_at": utc_now(),
        "questions": [
            {"text": "Capitale d'Italia?", "options": ["Roma", "Milano"], "correct_index": 0},
            {"text": "2+2?", "options": ["3", "4"], "correct_index": 1},
        ],
    })
    qid = str(quiz.inserted_id)
    athlete = await db.athletes.find_one({"sport_id": "calcio", "status": "ACTIVE"})

    token = create_access_token(user_id=str(uid))
    H = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30) as c:
        # streak
        r = await c.post(f"{API}/engagement/streak/claim", headers=H)
        ok(r.status_code == 200, f"streak claim 200 ({r.status_code} {r.text[:100]})")
        b = r.json()
        ok(b["claimed"] is True and b["reward_amount"] >= 1.0, f"streak reward ({b['reward_amount']})")
        # secondo claim stesso giorno -> non riaccredita
        b2 = (await c.post(f"{API}/engagement/streak/claim", headers=H)).json()
        ok(b2["claimed"] is False, "streak: secondo claim stesso giorno bloccato")

        # quizzes: NON deve esporre correct_index
        qz = (await c.get(f"{API}/engagement/quizzes", headers=H)).json()
        raw = str(qz)
        ok("correct_index" not in raw, "quizzes: correct_index NON esposto")
        ok(qz["count"] >= 1, f"quizzes: {qz['count']} attivi")

        # quiz attempt (1 giusta, 1 giusta -> perfect)
        r = await c.post(f"{API}/engagement/quizzes/{qid}/attempt", headers=H,
                         json={"answers": [0, 1]})
        ok(r.status_code == 200, f"quiz attempt 200 ({r.status_code} {r.text[:100]})")
        qa = r.json()
        ok(qa["correct"] == 2 and qa["perfect"] is True, "quiz: 2/2 perfect")
        ok(qa["reward_amount"] >= 2.0, f"quiz reward ({qa['reward_amount']})")
        # doppio tentativo -> bloccato
        r2 = await c.post(f"{API}/engagement/quizzes/{qid}/attempt", headers=H, json={"answers": [0, 1]})
        ok(r2.status_code == 400 and r2.json()["detail"]["error_code"] == "quiz.already_attempted",
           "quiz: doppio tentativo bloccato")

        # prediction
        r = await c.post(f"{API}/engagement/predictions", headers=H,
                         json={"athlete_id": str(athlete["_id"]), "direction": "up"})
        ok(r.status_code == 200, f"prediction 200 ({r.status_code} {r.text[:100]})")
        pr = r.json()
        ok(pr["ok"] and pr["direction"] == "up", "prediction creata")
        lst = (await c.get(f"{API}/engagement/predictions", headers=H)).json()
        ok(lst["count"] >= 1, f"predictions list ({lst['count']})")

    print("\nSMOKE FASE 6: VERDE")
    close_db()


if __name__ == "__main__":
    asyncio.run(main())
