"""CLI: simula N giornate sintetiche → apply_tick → storico prezzi (Fase 2b).

Dà MOVIMENTO alla borsa nell'MVP (sparkline non vuote, utile anche per testare la
Fase 3 senza utenti reali). Eventi SINTETICI deterministici per (atleta, giornata),
scalati da ruolo + score_performance. NESSUNA pretesa di realismo (DECISIONS.md 2b).

Uso (dalla cartella backend/):
    python -m app.cli.simulate_rounds --rounds 10
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import sys

from app.core.db import close_db, get_db, init_db
from app.models.common import utc_now
from app.pricing.engine import apply_tick
from app.pricing.performance import MatchPerformance, performance_pct

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("simulate_cli")

_GOL_PROB = {"ATT": 0.45, "CC": 0.22, "DIF": 0.10, "POR": 0.0}
_ASSIST_PROB = {"ATT": 0.30, "CC": 0.30, "DIF": 0.15, "POR": 0.02}


def _unit(key: str) -> float:
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big") / 2**64


def synthetic_round_performance(athlete: dict, round_idx: int) -> MatchPerformance:
    """Genera una giornata sintetica deterministica per l'atleta."""
    role = athlete["role"]
    score = float(athlete.get("score_performance", 1.0))
    minutaggio = float(athlete.get("minutaggio_pct", 0.7))
    base = f"sim:{athlete['_id']}:{round_idx}:"

    def u(tag: str) -> float:
        return _unit(base + tag)

    # gioca?
    if u("plays") > minutaggio + 0.10:
        return MatchPerformance(minuti=int(u("bench") * 25))  # spezzone/panchina

    minuti = 90 if u("full") < 0.7 else 60 + int(u("part") * 29)

    gol_p = _GOL_PROB[role] * score
    assist_p = _ASSIST_PROB[role] * score
    gol_fatti = (1 if u("g1") < gol_p else 0) + (1 if u("g2") < gol_p * 0.25 else 0)
    assist = 1 if u("a") < assist_p else 0
    ammonizioni = (1 if u("y1") < 0.16 else 0) + (1 if u("y2") < 0.02 else 0)
    espulso = u("red") < 0.01
    gol_subiti = 0 if u("cs") < 0.4 else (1 if u("c1") < 0.7 else 2)

    rigori_parati = 1 if role == "POR" and u("rp") < 0.06 else 0
    rigori_segnati = 1 if role in ("ATT", "CC") and u("ps") < 0.05 else 0

    voto = None
    if role == "POR":
        voto = round(7.5 - gol_subiti * 0.7 + rigori_parati * 0.6 + u("v") * 0.8, 1)

    return MatchPerformance(
        minuti=minuti,
        gol_fatti=gol_fatti,
        gol_subiti=gol_subiti,
        ammonizioni=ammonizioni,
        espulso=espulso,
        assist=assist,
        rigori_segnati=rigori_segnati,
        rigori_parati=rigori_parati,
        voto=voto,
    )


async def simulate_rounds(db, n_rounds: int, *, sport_id: str = "calcio") -> dict:
    """Applica n_rounds di tick sintetici a tutti gli atleti; scrive price_history."""
    athletes = await db.athletes.find(
        {"sport_id": sport_id, "status": "ACTIVE"}
    ).to_list(length=10_000)

    moves = 0
    for rnd in range(1, n_rounds + 1):
        for a in athletes:
            perf = synthetic_round_performance(a, rnd)
            pct = performance_pct(a["role"], perf)
            res = apply_tick(
                prezzo_corrente=a["prezzo_corrente_crediti"],
                prezzo_iniziale=a["prezzo_iniziale_crediti"],
                perf_pct=pct,
            )
            a["prezzo_corrente_crediti"] = res.new_price
            await db.athletes.update_one(
                {"_id": a["_id"]},
                {"$set": {"prezzo_corrente_crediti": res.new_price, "updated_at": utc_now()}},
            )
            await db.price_history.insert_one({
                "athlete_id": a["_id"],
                "round": rnd,
                "prezzo": res.new_price,
                "perf_pct": pct,
                "floored": res.floored,
                "ts": utc_now(),
            })
            if pct != 0.0:
                moves += 1

    return {
        "rounds": n_rounds,
        "athletes": len(athletes),
        "history_points": n_rounds * len(athletes),
        "moves": moves,
    }


async def main(n_rounds: int) -> int:
    init_db()
    db = get_db()
    stats = await simulate_rounds(db, n_rounds)
    logger.info(
        "DONE | rounds=%d | athletes=%d | history_points=%d | moves=%d",
        stats["rounds"], stats["athletes"], stats["history_points"], stats["moves"],
    )
    close_db()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=10)
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.rounds)))
