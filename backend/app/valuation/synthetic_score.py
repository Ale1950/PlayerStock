"""Score / team-tier / minutaggio SINTETICI e DETERMINISTICI (Fase 2b).

Segnaposto per "dar vita" al motore di valutazione nell'MVP finché non arrivano
statistiche reali (DECISIONS.md Fase 2b). Derivati per hash dall'identità del
giocatore/squadra → riproducibili, nessun RNG globale, nessuna pretesa di accuratezza.
"""
from __future__ import annotations

import hashlib
import math

# Tier squadra → fattore_squadra (dentro la banda [SQUADRA_MIN, SQUADRA_MAX])
TEAM_TIER_FACTOR: dict[str, float] = {"top": 1.25, "mid": 1.00, "weak": 0.93}

_SCORE_MEAN = 1.0
_SCORE_SD = 0.28


def _unit(key: str) -> float:
    """Pseudo-uniforme deterministica in [0, 1) dall'hash della chiave."""
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def synthetic_score(role: str, external_id: str) -> float:
    """Score performance ~N(1.0, 0.28) clampato a [0.5, 2.0]. Deterministico per (ruolo, id)."""
    u1 = _unit(f"score:{role}:{external_id}:a")
    u2 = _unit(f"score:{role}:{external_id}:b")
    # Box-Muller → normale standard
    z = math.sqrt(-2.0 * math.log(u1 + 1e-12)) * math.cos(2.0 * math.pi * u2)
    score = _SCORE_MEAN + _SCORE_SD * z
    return max(0.5, min(2.0, round(score, 3)))


def synthetic_team_tier(team_real_id: str) -> float:
    """Assegna un tier squadra deterministico → fattore_squadra. ~30% top, 40% mid, 30% weak."""
    bucket = int.from_bytes(
        hashlib.sha256(f"team:{team_real_id}".encode("utf-8")).digest()[:4], "big"
    ) % 10
    if bucket < 3:
        return TEAM_TIER_FACTOR["top"]
    if bucket < 7:
        return TEAM_TIER_FACTOR["mid"]
    return TEAM_TIER_FACTOR["weak"]


def synthetic_minutaggio(external_id: str) -> float:
    """Minutaggio % deterministico in [0.40, 1.0] (titolari vs rotazione)."""
    return round(0.40 + 0.60 * _unit(f"min:{external_id}"), 2)
