"""Valuation engine: valore iniziale + prezzo iniziale dell'atleta (Fase 2).

ValoreIniziale = K_GLOBAL × BASE_RUOLO[r] × f_score × f_età × f_minutaggio × f_squadra
prezzo_iniziale = ValoreIniziale / FLOAT_AZIONI_PER_GIOCATORE
"""
from __future__ import annotations

from app.config.pricing_constants import FLOAT_AZIONI_PER_GIOCATORE
from app.config.valuation_constants import (
    BASE_RUOLO,
    DEFAULT_FATTORE_SQUADRA,
    K_GLOBAL,
    clamp_fattore_squadra,
    fattore_eta,
    fattore_minutaggio,
    fattore_score,
)


def valuation(
    *,
    role: str,
    score: float,
    eta: int | None,
    minutaggio_pct: float,
    fattore_squadra: float = DEFAULT_FATTORE_SQUADRA,
) -> float:
    """Valore iniziale dell'atleta in Crediti."""
    return (
        K_GLOBAL
        * BASE_RUOLO[role]
        * fattore_score(score)
        * fattore_eta(eta)
        * fattore_minutaggio(minutaggio_pct)
        * clamp_fattore_squadra(fattore_squadra)
    )


def prezzo_iniziale(
    *,
    role: str,
    score: float,
    eta: int | None,
    minutaggio_pct: float,
    fattore_squadra: float = DEFAULT_FATTORE_SQUADRA,
) -> float:
    """Prezzo iniziale dell'azione = valore iniziale / float quote."""
    v = valuation(
        role=role,
        score=score,
        eta=eta,
        minutaggio_pct=minutaggio_pct,
        fattore_squadra=fattore_squadra,
    )
    return v / FLOAT_AZIONI_PER_GIOCATORE
