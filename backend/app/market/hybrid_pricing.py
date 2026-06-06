"""Prezzo IBRIDO (Fase 3b): impatto del trading + rientro verso l'àncora.

Funzioni PURE (nessun accesso DB), testabili in isolamento.

  prezzo_equo (àncora) = ValoreIniziale / FLOAT, si muove col rendimento (Fase 2).
  deviazione (per atleta) parte da 0:
      buy q  → += K × (q / FLOAT)
      sell q → -= K × (q / FLOAT)        clamp a ±DEVIAZIONE_CAP
  rientro LAZY (mean reversion), calcolato alla lettura:
      deviazione_ora = deviazione_ultima × e^(-λ·Δt)
  prezzo_mercato = clamp( prezzo_equo × (1 + deviazione_ora), floor, tetto )
      floor = FLOOR_PCT_PREZZO_INIZIALE × prezzo_iniziale
      tetto = prezzo_equo × (1 + DEVIAZIONE_CAP)   (limite anti-fuga via cap deviazione)
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Literal

from app.config.pricing_constants import (
    DEVIAZIONE_CAP,
    FLOAT_AZIONI_PER_GIOCATORE,
    FLOOR_PCT_PREZZO_INIZIALE,
    K_IMPATTO_TRADING,
    LAMBDA_DEVIAZIONE,
)


def decay_deviation(dev_last: float, dt_seconds: float, lam: float = LAMBDA_DEVIAZIONE) -> float:
    """Rientro esponenziale verso 0: dev_last × e^(-λ·Δt). Δt<0 → invariato."""
    if dt_seconds <= 0:
        return dev_last
    return dev_last * math.exp(-lam * dt_seconds)


def apply_impact(
    dev_now: float,
    side: Literal["buy", "sell"],
    qty: int,
    float_qty: int = FLOAT_AZIONI_PER_GIOCATORE,
    k: float = K_IMPATTO_TRADING,
    cap: float = DEVIAZIONE_CAP,
) -> float:
    """Aggiorna la deviazione per un ordine. buy alza, sell abbassa. Clamp ±cap."""
    impact = k * (qty / float_qty)
    new = dev_now + impact if side == "buy" else dev_now - impact
    return max(-cap, min(cap, new))


def market_price(
    prezzo_equo: float,
    deviazione: float,
    prezzo_iniziale: float,
    floor_pct: float = FLOOR_PCT_PREZZO_INIZIALE,
    cap: float = DEVIAZIONE_CAP,
) -> float:
    """prezzo_mercato = clamp(prezzo_equo × (1+deviazione), floor, tetto)."""
    dev = max(-cap, min(cap, deviazione))
    candidate = prezzo_equo * (1.0 + dev)
    floor = floor_pct * prezzo_iniziale
    tetto = prezzo_equo * (1.0 + cap)
    return max(floor, min(tetto, candidate))


def _naive_utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def effective_deviation(athlete: dict, now: datetime, lam: float = LAMBDA_DEVIAZIONE) -> float:
    """Deviazione corrente dell'atleta = ultima × decadimento fino a `now`."""
    dev_last = athlete.get("deviazione", 0.0)
    ts = athlete.get("deviazione_ts")
    if ts is None:
        return dev_last
    dt = (_naive_utc(now) - _naive_utc(ts)).total_seconds()
    return decay_deviation(dev_last, dt, lam)


def anchor_price(athlete: dict) -> float:
    """Prezzo equo (àncora). Fallback al prezzo corrente per atleti pre-migrazione."""
    return athlete.get("prezzo_equo_eur") or athlete["prezzo_corrente_eur"]


def current_market_price(athlete: dict, now: datetime, lam: float = LAMBDA_DEVIAZIONE) -> float:
    """Prezzo di mercato corrente dell'atleta, con deviazione decaduta fino a `now`."""
    dev_now = effective_deviation(athlete, now, lam)
    return market_price(anchor_price(athlete), dev_now, athlete["prezzo_iniziale_eur"])
