"""Regole pure del mercato: cap 3%, holding 7gg FIFO, fee 3.5%.

Nessun accesso al DB: funzioni testabili in isolamento.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config.pricing_constants import (
    CAP_UTENTE_AZIONI,
    FEE_BUYER_PCT,
    FEE_SELLER_PCT,
    HOLDING_MINIMO_GIORNI,
)
from app.core.errors import err_bad_request


def _naive_utc(dt: datetime) -> datetime:
    """Normalizza a UTC naive (Mongo restituisce datetime senza tzinfo)."""
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def assert_within_cap(*, current_qty: int, add_qty: int) -> None:
    """Cap utente 3% del float = CAP_UTENTE_AZIONI quote per atleta."""
    if current_qty + add_qty > CAP_UTENTE_AZIONI:
        raise err_bad_request(
            "market.cap_exceeded",
            f"Superato il cap del 3% ({CAP_UTENTE_AZIONI} quote) per questo atleta",
            extra={"current_qty": current_qty, "add_qty": add_qty, "cap": CAP_UTENTE_AZIONI},
        )


def sellable_quantity(lots: list[dict], now: datetime) -> int:
    """Quote vendibili = lotti con holding ≥ HOLDING_MINIMO_GIORNI giorni."""
    cutoff = _naive_utc(now) - timedelta(days=HOLDING_MINIMO_GIORNI)
    return sum(lot["qty"] for lot in lots if _naive_utc(lot["acquired_at"]) <= cutoff)


def consume_lots_fifo(lots: list[dict], qty: int) -> list[dict]:
    """Rimuove `qty` quote dai lotti più vecchi (FIFO). Ritorna i lotti residui."""
    remaining: list[dict] = []
    to_consume = qty
    for lot in sorted(lots, key=lambda x: _naive_utc(x["acquired_at"])):
        if to_consume <= 0:
            remaining.append(lot)
            continue
        take = min(lot["qty"], to_consume)
        if lot["qty"] > take:
            remaining.append({**lot, "qty": lot["qty"] - take})
        to_consume -= take
    if to_consume > 0:
        raise ValueError("qty richiesta superiore alle quote possedute")
    return remaining


def consume_lots_fifo_with_cost(lots: list[dict], qty: int) -> tuple[list[dict], float]:
    """Come consume_lots_fifo ma ritorna anche il COSTO BASE delle quote vendute
    (Σ qty_consumata × price del lotto), per il P&L realizzato."""
    remaining: list[dict] = []
    to_consume = qty
    cost = 0.0
    for lot in sorted(lots, key=lambda x: _naive_utc(x["acquired_at"])):
        if to_consume <= 0:
            remaining.append(lot)
            continue
        take = min(lot["qty"], to_consume)
        cost += take * (lot.get("price", 0.0) or 0.0)
        if lot["qty"] > take:
            remaining.append({**lot, "qty": lot["qty"] - take})
        to_consume -= take
    if to_consume > 0:
        raise ValueError("qty richiesta superiore alle quote possedute")
    return remaining, cost


# ───── fee / costi (gross = qty × prezzo di quotazione) ─────
def buy_gross(qty: int, price: float) -> float:
    return qty * price


def fee_buyer(qty: int, price: float) -> float:
    return qty * price * FEE_BUYER_PCT


def buy_cost(qty: int, price: float) -> float:
    """Esborso acquirente = gross + fee 3.5%."""
    return qty * price * (1.0 + FEE_BUYER_PCT)


def sell_gross(qty: int, price: float) -> float:
    return qty * price


def fee_seller(qty: int, price: float) -> float:
    return qty * price * FEE_SELLER_PCT


def sell_proceeds(qty: int, price: float) -> float:
    """Accredito venditore = gross − fee 3.5%."""
    return qty * price * (1.0 - FEE_SELLER_PCT)
