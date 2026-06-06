"""Statistiche sportive SINTETICHE per giocatore/settimana (Fase Design Parte 2).

Deterministiche (hash dell'identità), CONSISTENTI con:
- lo SCORE esistente (alto → più gol/assist/parate) — NON rigenera lo score, lo LEGGE;
- il RUOLO (ATT→gol, POR→parate, niente parate per i giocatori di movimento);
- il MINUTAGGIO (chi gioca meno ha meno presenze).

Segnaposto come `synthetic_score` (DECISIONS Fase 2b): nessuna pretesa di realismo,
servono a riempire la UI con dati interni coerenti senza dati web sui giocatori.

> PROPOSTA (NON applicata): legare score↔eventi via i coefficienti di `Gioco 5.xls`
> (DRIVERS in pricing_constants) farebbe sì che le stat MUOVANO il prezzo come gli
> eventi reali. Qui invece sono puramente descrittive (non toccano il pricing tarato).
> Da valutare in una fase dati reali.
"""
from __future__ import annotations

import hashlib

_GOL_PROB = {"ATT": 0.45, "CC": 0.22, "DIF": 0.10, "POR": 0.0}
_ASSIST_PROB = {"ATT": 0.30, "CC": 0.30, "DIF": 0.15, "POR": 0.02}
_SEASON_WEEKS = 12


def _u(key: str) -> float:
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big") / 2**64


def synthetic_weekly_stats(*, role: str, external_id: str, score: float, minutaggio: float,
                           weeks: int = _SEASON_WEEKS) -> dict:
    """Linea ultima settimana + totali stagionali, deterministici e coerenti."""
    s = max(0.5, min(2.0, float(score)))
    eid = str(external_id)
    season = {"presenze": 0, "minuti": 0, "gol": 0, "assist": 0, "parate": 0, "ammonizioni": 0}
    last: dict = {}
    for w in range(1, weeks + 1):
        def u(tag: str) -> float:
            return _u(f"ws:{eid}:{w}:{tag}")

        if u("plays") > minutaggio + 0.10:
            last = {"week": w, "minuti": 0, "gol": 0, "assist": 0,
                    "parate": (0 if role == "POR" else None), "ammonizioni": 0, "voto": None}
            continue

        minuti = 90 if u("full") < 0.7 else 60 + int(u("part") * 29)
        pg = min(0.95, _GOL_PROB[role] * s)
        gol = (1 if u("g1") < pg else 0) + (1 if u("g2") < pg * 0.4 else 0)
        pa = min(0.95, _ASSIST_PROB[role] * s)
        assist = 1 if u("a") < pa else 0
        amm = 1 if u("y") < 0.16 else 0
        parate = None
        voto = None
        if role == "POR":
            pp = min(0.90, 0.5 * s)
            parate = sum(1 for k in ("p1", "p2", "p3", "p4", "p5") if u(k) < pp)
            voto = round(6.0 + u("v") * 2.5 + parate * 0.15, 1)
        last = {"week": w, "minuti": minuti, "gol": gol, "assist": assist,
                "parate": parate, "ammonizioni": amm, "voto": voto}
        season["presenze"] += 1
        season["minuti"] += minuti
        season["gol"] += gol
        season["assist"] += assist
        season["ammonizioni"] += amm
        if parate:
            season["parate"] += parate
    return {"last_week": last, "season": season}


def compact_weekly_stats(athlete: dict) -> dict:
    """Forma compatta per la lista mercato: totali stagionali essenziali."""
    full = synthetic_weekly_stats(
        role=athlete["role"],
        external_id=str(athlete.get("source_external_id") or athlete.get("_id")),
        score=float(athlete.get("score_performance", 1.0)),
        minutaggio=float(athlete.get("minutaggio_pct", 0.7)),
    )
    se = full["season"]
    return {
        "gol": se["gol"],
        "assist": se["assist"],
        "parate": se["parate"] if athlete["role"] == "POR" else None,
        "presenze": se["presenze"],
    }
