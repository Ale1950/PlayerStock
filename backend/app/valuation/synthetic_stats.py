"""Statistiche sportive MOSTRATE — lettore dell'accumulo round (UNICA fonte, D10).

Le stat NON sono più rigenerate qui: sono la SOMMA degli eventi per-round che muovono
il prezzo (`market/rounds.run_round` accumula `season_stats` + `last_round_stats` sul
doc atleta). Così ciò che vedi a schermo == ciò che ha mosso il prezzo. Niente
contraddizioni. Atleti non ancora "giocati" → stat a zero (si riempiono coi round).
"""
from __future__ import annotations

_EMPTY_SEASON = {"presenze": 0, "minuti": 0, "gol": 0, "assist": 0, "parate": 0, "ammonizioni": 0}


def season_stats_of(athlete: dict) -> dict:
    s = dict(_EMPTY_SEASON)
    s.update({k: int(v or 0) for k, v in (athlete.get("season_stats") or {}).items() if k in s})
    return s


def last_round_of(athlete: dict) -> dict:
    return athlete.get("last_round_stats") or {
        "minuti": 0, "gol": 0, "assist": 0,
        "parate": (0 if athlete.get("role") == "POR" else None), "ammonizioni": 0, "voto": None,
    }


def synthetic_weekly_stats(athlete: dict) -> dict:
    """Ultimo round + totali stagionali, dall'accumulo persistito sull'atleta."""
    return {"last_week": last_round_of(athlete), "season": season_stats_of(athlete)}


def compact_weekly_stats(athlete: dict) -> dict:
    """Forma compatta per la lista mercato: totali stagionali essenziali."""
    se = season_stats_of(athlete)
    return {
        "gol": se["gol"],
        "assist": se["assist"],
        "parate": se["parate"] if athlete.get("role") == "POR" else None,
        "presenze": se["presenze"],
    }
