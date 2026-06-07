"""Performance% settimanale: somma dei driver oggettivi, poi clamp per ruolo."""
from __future__ import annotations

from dataclasses import dataclass

from app.config.pricing_constants import RANGE_CLAMP
from app.pricing.drivers import band_count, band_minuti, band_voto_portiere, coeff


@dataclass
class MatchPerformance:
    """Statistiche settimanali aggregate di un atleta (input oggettivo)."""
    minuti: int = 0
    gol_fatti: int = 0
    gol_subiti: int = 0          # gol subiti dalla squadra
    ammonizioni: int = 0
    espulso: bool = False
    assist: int = 0
    rigori_segnati: int = 0
    rigori_sbagliati: int = 0
    rigori_parati: int = 0
    autoreti: int = 0
    voto: float | None = None    # solo portiere


def raw_performance_pct(role: str, perf: MatchPerformance) -> float:
    """Somma dei contributi driver (NON clampata)."""
    total = 0.0
    total += coeff("MINUTI_GIOCATI", role, band_minuti(perf.minuti))

    count_drivers = [
        ("GOL_FATTI", perf.gol_fatti),
        ("GOL_SUBITI", perf.gol_subiti),
        ("AMMONIZIONE", perf.ammonizioni),
        ("ESPULSIONE", 1 if perf.espulso else 0),
        ("ASSIST", perf.assist),
        ("RIGORI_SEGNATI", perf.rigori_segnati),
        ("RIGORI_SBAGLIATI", perf.rigori_sbagliati),
        ("RIGORI_PARATI", perf.rigori_parati),
        ("AUTORETE", perf.autoreti),
    ]
    for key, n in count_drivers:
        band = band_count(key, n)
        if band is not None:
            total += coeff(key, role, band)

    if role == "POR" and perf.voto is not None:
        total += coeff("VOTO_PORTIERE", role, band_voto_portiere(perf.voto))

    return total


def clamp_perf(role: str, value: float) -> float:
    rng = RANGE_CLAMP[role]
    return max(rng["down"], min(rng["up"], value))


def performance_pct(role: str, perf: MatchPerformance, *, gain: float = 1.0) -> float:
    """Performance% del round = somma driver × gain, poi clampata al range ruolo.

    `gain` (default 1.0 → golden invariato) amplifica i movimenti in modalità veloce.
    Il clamp RANGE_CLAMP è applicato DOPO il gain → resta sempre rispettato.
    """
    return clamp_perf(role, raw_performance_pct(role, perf) * gain)


def surprise_pct(role: str, raw_actual: float, expected: float, *, gain: float = 1.0) -> float:
    """Movimento di prezzo su SORPRESA = (punteggio reale − atteso) × gain, poi clamp.

    Il PUNTEGGIO (raw_performance_pct, coeff. Gioco 5) NON cambia: si sottrae solo la
    media attesa (già "prezzata" dalla qualità) → chi rende come da attese ≈ fermo,
    chi supera/delude sale/scende. Clamp RANGE_CLAMP invariato.
    """
    return clamp_perf(role, (raw_actual - expected) * gain)
