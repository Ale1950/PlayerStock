"""Selezione banda + lookup coefficiente per i driver di pricing.

Le tabelle dei coefficienti stanno in `config.pricing_constants.DRIVERS` (estratte da
`Gioco 5.xls` / Serie 1). Qui solo la logica di mapping evento→banda e il lookup.
"""
from __future__ import annotations

from app.config.pricing_constants import DRIVERS

# Driver con banda ZERO esplicita (l'assenza dell'evento ha comunque un effetto)
_THREE_STATE = {"GOL_FATTI", "GOL_SUBITI", "ASSIST", "RIGORI_SBAGLIATI"}
# Driver senza banda ZERO: count 0 → nessun contributo
_NO_ZERO_123 = {"RIGORI_SEGNATI", "RIGORI_PARATI"}


def band_minuti(minuti: int) -> str:
    if minuti > 60:
        return "GT_60"
    if minuti > 45:
        return "BETWEEN_45_60"
    return "LE_45"


def band_voto_portiere(voto: float) -> str:
    if voto < 6:
        return "LT_6"
    if voto < 8:
        return "B6_7"
    return "GE_8"


def band_count(driver_key: str, n: int) -> str | None:
    """Mappa un conteggio evento alla banda del driver. None = nessun contributo."""
    if driver_key in _THREE_STATE:
        if n <= 0:
            return "ZERO"
        if n == 1:
            return "ONE"
        return "GE_2"
    if driver_key == "AMMONIZIONE":
        if n <= 0:
            return "ZERO"
        if n == 1:
            return "ONE"
        return "TWO"
    if driver_key == "ESPULSIONE":
        return "ONE" if n >= 1 else None
    if driver_key in _NO_ZERO_123:
        if n <= 0:
            return None
        if n == 1:
            return "ONE"
        if n == 2:
            return "TWO"
        return "THREE"
    if driver_key == "AUTORETE":
        if n <= 0:
            return None
        if n == 1:
            return "ONE"
        if n == 2:
            return "TWO"
        return "GE_3"
    raise KeyError(f"driver senza mapping count: {driver_key}")


def coeff(driver_key: str, role: str, band: str) -> float:
    return DRIVERS[driver_key][role][band]
