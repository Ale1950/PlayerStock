"""Tick di prezzo: nuovo_prezzo = vecchio × (1 + perf% + mkt% + eng%), floor 10%.

Il prezzo interno è mantenuto a PIENA precisione (i 4 decimali sono solo display,
DISPLAY_DECIMALS). Insieme al prezzo si espone sempre la variazione % (`pct_change`),
così i movimenti dei titoli a basso prezzo restano visibili.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config.pricing_constants import FLOOR_PCT_PREZZO_INIZIALE


@dataclass
class TickResult:
    new_price: float       # piena precisione (NON arrotondato)
    pct_change: float      # (new - old) / old
    floored: bool          # True se ha toccato il floor


def apply_tick(
    *,
    prezzo_corrente: float,
    prezzo_iniziale: float,
    perf_pct: float,
    mercato_pct: float = 0.0,
    engagement_pct: float = 0.0,
) -> TickResult:
    """Applica un tick di prezzo. mkt%/eng% = 0 in Fase 2 (Fasi 3/6)."""
    delta = perf_pct + mercato_pct + engagement_pct
    candidate = prezzo_corrente * (1.0 + delta)

    floor = FLOOR_PCT_PREZZO_INIZIALE * prezzo_iniziale
    floored = candidate < floor
    new_price = floor if floored else candidate

    pct_change = (new_price - prezzo_corrente) / prezzo_corrente if prezzo_corrente else 0.0
    return TickResult(new_price=new_price, pct_change=pct_change, floored=floored)
