"""Quiz a tema MERCATO (Engage) — domande generate dai DATI veri via /api/stats.

Persistito in `db.quizzes` (1 quiz/giorno, idempotente) così il punteggio passa per il
flusso quiz esistente (`submit_quiz_attempt` → SOLO € via faucet; nessun NACKL).
Le opzioni sono ordinate deterministicamente; `correct_index` MAI esposto al client.
"""
from __future__ import annotations

import datetime as dt

from app.models.common import utc_now
from app.modules.stats.service import market_overview

_ROLE_LABEL = {"POR": "Portiere", "DIF": "Difensore", "CC": "Centrocampista", "ATT": "Attaccante"}


def _q(text: str, options: list[str], correct: str) -> dict:
    opts = sorted(set(options))
    if correct not in opts:
        opts = [correct, *opts][:4]
    return {"text": text, "options": opts, "correct_index": opts.index(correct)}


async def _build_questions(db, now: dt.datetime) -> list[dict]:
    ov = await market_overview(db, now=now)
    qs: list[dict] = []

    gainers = [m for m in ov.get("top_gainers", []) if m.get("display_label")]
    if len(gainers) >= 2:
        qs.append(_q("Chi è il TOP GAINER della settimana?",
                     [g["display_label"] for g in gainers[:4]], gainers[0]["display_label"]))

    dist = ov.get("price_distribution", {})
    if dist:
        top_role = max(dist.items(), key=lambda kv: kv[1].get("avg", 0))[0]
        qs.append(_q("Quale RUOLO ha il prezzo medio più alto?",
                     [_ROLE_LABEL.get(r, r) for r in dist], _ROLE_LABEL.get(top_role, top_role)))

    n = ov.get("active_count", 0)
    qs.append(_q("Quanti ATLETI ATTIVI ci sono sul mercato?",
                 [str(n), str(max(0, n - 50)), str(n + 50), str(n + 120)], str(n)))
    return qs


async def get_or_create_market_quiz(db, *, now: dt.datetime | None = None) -> dict:
    """Quiz mercato del giorno (idempotente). Ritorna {id, title, questions(safe), already_attempted}."""
    now = now or utc_now()
    day = now.date().isoformat()
    quiz = await db.quizzes.find_one({"market_quiz_day": day})
    if not quiz:
        questions = await _build_questions(db, now)
        res = await db.quizzes.insert_one({
            "title": f"Quiz Mercato · {day}", "description": "Domande generate dai dati di mercato",
            "questions": questions, "active": True, "market_quiz_day": day, "created_at": now,
        })
        quiz = await db.quizzes.find_one({"_id": res.inserted_id})
    return {
        "id": str(quiz["_id"]),
        "title": quiz.get("title"),
        "questions": [{"id": i, "text": q.get("text"), "options": q.get("options", [])}
                      for i, q in enumerate(quiz.get("questions", []))],
    }
