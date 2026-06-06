"""CLI: seed di quiz di calcio per la tab Engage (Fase 6). Idempotente (upsert per titolo).

Uso (dalla cartella backend/):
    python -m app.cli.seed_quizzes
"""
from __future__ import annotations

import asyncio
import logging

from app.core.db import close_db, get_db, init_db
from app.models.common import utc_now

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_quizzes")

# Domande generiche di cultura calcistica (nessun dato proprietario / L2 non coinvolta).
QUIZZES: list[dict] = [
    {
        "title": "Basi del calcio",
        "description": "Quiz introduttivo sulle regole.",
        "questions": [
            {"text": "Quanti giocatori per squadra in campo?", "options": ["9", "10", "11", "12"], "correct_index": 2},
            {"text": "Durata regolamentare di una partita?", "options": ["60'", "80'", "90'", "120'"], "correct_index": 2},
            {"text": "Quanti punti vale una vittoria in Serie A?", "options": ["1", "2", "3", "4"], "correct_index": 2},
        ],
    },
    {
        "title": "Ruoli in campo",
        "description": "Conosci i ruoli?",
        "questions": [
            {"text": "Chi può usare le mani in area?", "options": ["Difensore", "Portiere", "Attaccante", "Arbitro"], "correct_index": 1},
            {"text": "Sigla del centrocampista nel gioco?", "options": ["POR", "DIF", "CC", "ATT"], "correct_index": 2},
            {"text": "Chi segna principalmente i gol?", "options": ["Portiere", "Difensore", "Attaccante", "Massaggiatore"], "correct_index": 2},
        ],
    },
    {
        "title": "Regole e arbitraggio",
        "description": "Cartellini e decisioni.",
        "questions": [
            {"text": "Quanti cartellini gialli portano all'espulsione?", "options": ["1", "2", "3", "4"], "correct_index": 1},
            {"text": "Cosa assegna l'arbitro per fallo grave in area?", "options": ["Corner", "Rimessa", "Rigore", "Fuorigioco"], "correct_index": 2},
            {"text": "La tecnologia che assiste l'arbitro?", "options": ["GPS", "VAR", "NFC", "GPS"], "correct_index": 1},
        ],
    },
    {
        "title": "Competizioni",
        "description": "Tornei e trofei.",
        "questions": [
            {"text": "Massima competizione europea per club?", "options": ["Europa League", "Champions League", "Conference", "Supercoppa"], "correct_index": 1},
            {"text": "Ogni quanti anni si gioca il Mondiale?", "options": ["2", "3", "4", "5"], "correct_index": 2},
            {"text": "Quante squadre in Serie A?", "options": ["18", "20", "22", "24"], "correct_index": 1},
        ],
    },
    {
        "title": "Numeri del calcio",
        "description": "Statistiche di base.",
        "questions": [
            {"text": "Quanti giocatori titolari + panchina max in distinta?", "options": ["11", "18", "23", "30"], "correct_index": 2},
            {"text": "Durata di un tempo supplementare?", "options": ["10'", "15'", "20'", "30'"], "correct_index": 1},
            {"text": "Quanti gol per una 'tripletta'?", "options": ["2", "3", "4", "5"], "correct_index": 1},
        ],
    },
]


async def main() -> int:
    init_db()
    db = get_db()
    now = utc_now()
    upserts = 0
    for q in QUIZZES:
        res = await db.quizzes.update_one(
            {"title": q["title"]},
            {"$set": {**q, "active": True, "updated_at": now},
             "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        if res.upserted_id or res.modified_count:
            upserts += 1
    total = await db.quizzes.count_documents({"active": True})
    logger.info("Quiz seedati/aggiornati: %d | quiz attivi totali: %d", upserts, total)
    close_db()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
