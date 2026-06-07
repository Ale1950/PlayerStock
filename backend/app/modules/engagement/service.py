"""Engagement service: pure functions + DB-backed orchestration.

Meccaniche:
- daily_login_streak: incrementa streak su accesso giornaliero, accredita reward
- quiz_attempt: completa quiz, valuta risposte, accredita reward (anti-doppio)
- prediction_submit: registra previsione su atleta (24h target), reward se indovinata
- prediction_settle: cron/admin valuta le previsioni scadute confrontando prezzi

CAP/anti-abuso:
- streak: 1 reward / giorno solare UTC per utente
- quiz: 1 reward / quiz_id / giorno per utente (anti-replay)
- prediction: max 3 predizioni aperte simultanee per utente
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from app.economy.credit_faucet import grant_engagement_credits
from app.models.common import utc_now

# ───────── COSTANTI REWARD (in EP — punti engagement → ricompensa in € via faucet) ─────────
# NB: il gioco NON assegna NACKL. Questi sono "engagement points" che alimentano il
# faucet € (grant_engagement_credits). I NACKL derivano solo dal mining/heartbeat.
REWARD_LOGIN_STREAK_BASE = 1.0
REWARD_LOGIN_STREAK_BONUS_PER_DAY = 0.2  # +20% per giorno consecutivo, cap a 7
REWARD_LOGIN_STREAK_CAP_DAYS = 7
REWARD_QUIZ_PER_CORRECT = 0.5
REWARD_QUIZ_PERFECT_BONUS = 1.0
REWARD_PREDICTION_CORRECT = 2.5
MAX_OPEN_PREDICTIONS_PER_USER = 3
PREDICTION_HORIZON_HOURS = 24


# ───────── PURE FUNCTIONS (testabili senza DB) ─────────

def compute_streak_reward(streak_days: int) -> float:
    """Engagement points (EP) per uno streak di N giorni → ricompensa in € (faucet)."""
    if streak_days < 1:
        return 0.0
    effective = min(streak_days, REWARD_LOGIN_STREAK_CAP_DAYS)
    return REWARD_LOGIN_STREAK_BASE * (1 + REWARD_LOGIN_STREAK_BONUS_PER_DAY * (effective - 1))


def is_same_utc_day(a: dt.datetime, b: dt.datetime) -> bool:
    return a.date() == b.date()


def is_consecutive_day(prev: dt.datetime, now: dt.datetime) -> bool:
    return (now.date() - prev.date()).days == 1


def evaluate_quiz(*, questions: list[dict], answers: list[int]) -> dict:
    """Valuta le risposte. `questions[i]['correct_index']` = indice corretto.
    `answers[i]` = indice scelto dall'utente. Restituisce {correct, total, score}.
    """
    if not questions:
        return {"correct": 0, "total": 0, "score": 0.0, "perfect": False}
    total = len(questions)
    correct = 0
    for i, q in enumerate(questions):
        chosen = answers[i] if i < len(answers) else -1
        if chosen == q.get("correct_index", -999):
            correct += 1
    perfect = (correct == total)
    return {
        "correct": correct, "total": total,
        "score": correct / total if total else 0.0, "perfect": perfect,
    }


def compute_quiz_reward(*, correct: int, perfect: bool) -> float:
    base = REWARD_QUIZ_PER_CORRECT * correct
    return base + (REWARD_QUIZ_PERFECT_BONUS if perfect else 0.0)


# ───────── DB-BACKED ORCHESTRATION ─────────

async def claim_daily_streak(db, user_id) -> dict:
    """Registra accesso giornaliero. Se nuovo giorno: incrementa streak e accredita reward.
    Se stesso giorno: ritorna stato senza accreditare."""
    now = utc_now()
    streak = await db.login_streaks.find_one({"user_id": user_id})

    if streak and is_same_utc_day(streak["last_claim_at"], now):
        return {
            "claimed": False, "reason": "already_claimed_today",
            "current_streak": streak["current_streak"],
            "longest_streak": streak.get("longest_streak", streak["current_streak"]),
        }

    if streak and is_consecutive_day(streak["last_claim_at"], now):
        new_streak = streak["current_streak"] + 1
    else:
        new_streak = 1  # reset (o primo accesso)

    reward = compute_streak_reward(new_streak)
    longest = max(streak.get("longest_streak", 0) if streak else 0, new_streak)

    await db.login_streaks.update_one(
        {"user_id": user_id},
        {"$set": {"current_streak": new_streak, "longest_streak": longest,
                  "last_claim_at": now, "updated_at": now},
         "$setOnInsert": {"user_id": user_id, "created_at": now}},
        upsert=True,
    )

    # SOLO ricompensa in € (faucet). NESSUN NACKL: il gioco non assegna mai NACKL
    # (i NACKL derivano unicamente dal mining/heartbeat — vincolo permanente).
    credit = await grant_engagement_credits(
        db, user_id=user_id, event_id=f"streak:{user_id}:{now.date().isoformat()}",
        ep=reward, now=now,
    )
    return {
        "claimed": True, "current_streak": new_streak, "longest_streak": longest,
        "reward_amount": reward, "credit_bonus": credit["credits"],
    }


async def submit_quiz_attempt(db, user_id, *, quiz_id: str, answers: list[int]) -> dict:
    """Esegue un tentativo di quiz. Anti-doppio: max 1 reward per quiz_id per utente."""
    from bson import ObjectId
    try:
        qid = ObjectId(quiz_id)
    except Exception:
        return {"ok": False, "error_code": "quiz.invalid_id"}

    quiz = await db.quizzes.find_one({"_id": qid, "active": True})
    if not quiz:
        return {"ok": False, "error_code": "quiz.not_found"}

    existing = await db.quiz_attempts.find_one({"user_id": user_id, "quiz_id": qid})
    if existing:
        return {"ok": False, "error_code": "quiz.already_attempted",
                "previous_score": existing.get("score"),
                "previous_correct": existing.get("correct")}

    result = evaluate_quiz(questions=quiz["questions"], answers=answers)
    reward = compute_quiz_reward(correct=result["correct"], perfect=result["perfect"])
    now = utc_now()

    credit_bonus = 0.0
    if reward > 0:
        # SOLO €: nessun accrual NACKL (NACKL = solo mining).
        credit = await grant_engagement_credits(
            db, user_id=user_id, event_id=f"quiz:{user_id}:{qid}", ep=reward, now=now,
        )
        credit_bonus = credit["credits"]

    await db.quiz_attempts.insert_one({
        "user_id": user_id, "quiz_id": qid,
        "answers": answers, "correct": result["correct"], "total": result["total"],
        "score": result["score"], "perfect": result["perfect"],
        "reward_amount": reward, "created_at": now,
    })
    return {
        "ok": True, "correct": result["correct"], "total": result["total"],
        "score": result["score"], "perfect": result["perfect"],
        "reward_amount": reward, "credit_bonus": credit_bonus,
    }


async def submit_prediction(db, user_id, *, athlete_id, direction: str) -> dict:
    """Predici se il prezzo di un atleta salirà ('up') o scenderà ('down') in 24h.
    Cap: max 3 predizioni aperte per utente."""
    if direction not in ("up", "down"):
        return {"ok": False, "error_code": "prediction.invalid_direction"}

    from bson import ObjectId
    try:
        aid = ObjectId(athlete_id)
    except Exception:
        return {"ok": False, "error_code": "athlete.invalid_id"}

    athlete = await db.athletes.find_one({"_id": aid, "status": "ACTIVE"})
    if not athlete:
        return {"ok": False, "error_code": "athlete.not_found"}

    open_count = await db.predictions.count_documents({"user_id": user_id, "status": "open"})
    if open_count >= MAX_OPEN_PREDICTIONS_PER_USER:
        return {"ok": False, "error_code": "prediction.too_many_open",
                "max": MAX_OPEN_PREDICTIONS_PER_USER}

    now = utc_now()
    base_price = float(athlete.get("prezzo_corrente_eur", 0.0))
    expires_at = now + dt.timedelta(hours=PREDICTION_HORIZON_HOURS)

    res = await db.predictions.insert_one({
        "user_id": user_id, "athlete_id": aid,
        "direction": direction, "base_price": base_price,
        "horizon_hours": PREDICTION_HORIZON_HOURS,
        "status": "open", "created_at": now, "expires_at": expires_at,
        "settled_at": None, "settled_price": None, "outcome": None,
        "reward_tx_id": None, "reward_amount": 0.0,
    })
    return {
        "ok": True, "prediction_id": str(res.inserted_id),
        "athlete_id": str(aid), "direction": direction,
        "base_price": base_price, "expires_at": expires_at,
    }


async def settle_expired_predictions(db, *, limit: int = 200) -> dict:
    """Job (admin/cron): chiude le predizioni scadute confrontando prezzo corrente.
    Accredita reward se indovinata. Idempotente (status: open → won/lost)."""
    now = utc_now()
    cursor = db.predictions.find({"status": "open", "expires_at": {"$lte": now}}).limit(limit)
    items = await cursor.to_list(length=limit)
    settled = 0
    won = 0
    for p in items:
        athlete = await db.athletes.find_one({"_id": p["athlete_id"]})
        if not athlete:
            await db.predictions.update_one(
                {"_id": p["_id"]},
                {"$set": {"status": "void", "settled_at": now}},
            )
            continue
        cur = float(athlete.get("prezzo_corrente_eur", 0.0))
        base = float(p["base_price"])
        direction = p["direction"]
        outcome = "won" if (
            (direction == "up" and cur > base) or
            (direction == "down" and cur < base)
        ) else "lost"
        reward_amt = 0.0
        if outcome == "won":
            reward_amt = REWARD_PREDICTION_CORRECT
            # SOLO €: nessun accrual NACKL (NACKL = solo mining).
            await grant_engagement_credits(
                db, user_id=p["user_id"], event_id=f"prediction:{p['_id']}",
                ep=REWARD_PREDICTION_CORRECT, now=now,
            )
            won += 1
        await db.predictions.update_one(
            {"_id": p["_id"]},
            {"$set": {"status": outcome, "settled_at": now, "settled_price": cur,
                      "outcome": outcome, "reward_amount": reward_amt, "reward_tx_id": None}},
        )
        settled += 1
    return {"settled": settled, "won": won, "lost": settled - won}


async def list_active_quizzes(db) -> list[dict]:
    cursor = db.quizzes.find({"active": True}).sort("created_at", -1).limit(20)
    items = await cursor.to_list(length=20)
    safe: list[dict] = []
    for q in items:
        # NEVER expose correct_index!
        safe_questions = [
            {"id": idx, "text": qq.get("text"), "options": qq.get("options", [])}
            for idx, qq in enumerate(q.get("questions", []))
        ]
        safe.append({
            "id": str(q["_id"]), "title": q.get("title"),
            "description": q.get("description"),
            "questions": safe_questions, "active": q.get("active", True),
        })
    return safe


async def get_my_predictions(db, user_id, *, status: str | None = None, limit: int = 50) -> list[dict]:
    filt = {"user_id": user_id}
    if status:
        filt["status"] = status
    cursor = db.predictions.find(filt).sort("created_at", -1).limit(limit)
    raw = await cursor.to_list(length=limit)
    out: list[dict] = []
    for p in raw:
        out.append({
            "id": str(p["_id"]), "athlete_id": str(p["athlete_id"]),
            "direction": p["direction"], "base_price": p["base_price"],
            "status": p["status"], "outcome": p.get("outcome"),
            "settled_price": p.get("settled_price"),
            "created_at": p["created_at"], "expires_at": p.get("expires_at"),
            "settled_at": p.get("settled_at"),
            "reward_amount": p.get("reward_amount", 0.0),
        })
    return out


async def engagement_overview(db, user_id) -> dict:
    """Aggrega tutte le meccaniche Engage per la schermata: streak · quiz mercato ·
    pronostici · missioni · sfida settimanale."""
    from bson import ObjectId

    from app.modules.engagement.challenges import weekly_challenge
    from app.modules.engagement.market_quiz import get_or_create_market_quiz
    from app.modules.engagement.missions import evaluate_missions
    from app.modules.engagement.news import market_news

    quiz = await get_or_create_market_quiz(db)
    attempted = await db.quiz_attempts.find_one({"user_id": user_id, "quiz_id": ObjectId(quiz["id"])}) is not None
    return {
        "streak": await get_streak_state(db, user_id),
        "market_quiz": {**quiz, "already_attempted": attempted},
        "predictions": {
            "open": await db.predictions.count_documents({"user_id": user_id, "status": "open"}),
            "recent": await get_my_predictions(db, user_id, limit=5),
        },
        "missions": await evaluate_missions(db, user_id),
        "challenge": await weekly_challenge(db, user_id),
        "news": await market_news(db, user_id),
    }


async def get_streak_state(db, user_id) -> dict:
    s = await db.login_streaks.find_one({"user_id": user_id})
    if not s:
        return {"current_streak": 0, "longest_streak": 0, "last_claim_at": None,
                "can_claim_today": True}
    now = utc_now()
    can_claim = not is_same_utc_day(s["last_claim_at"], now)
    return {
        "current_streak": s.get("current_streak", 0),
        "longest_streak": s.get("longest_streak", 0),
        "last_claim_at": s["last_claim_at"], "can_claim_today": can_claim,
        "next_reward_estimate": compute_streak_reward(
            s.get("current_streak", 0) + 1 if can_claim else s.get("current_streak", 0)
        ),
    }
