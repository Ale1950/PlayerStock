"""
PlayerStock — Valuation constants (Fase 1 = placeholder).

⚠️ Valori esatti calibrati in FASE 2 (Claude Code) leggendo `Gioco 5.xls`.
Qui in Fase 1 servono i defaults per la seed dei 400 giocatori; il calcolo
puntuale del `valore_iniziale_crediti` di ogni atleta è demandato a Fase 2.

Formula consolidata (PROJECT_SPEC.md §5):
    ValoreIniziale = BaseRuolo × ScorePerformance × FattoreEtà × FattoreMinutaggio × FattoreSquadra × K
"""
from __future__ import annotations

# ───────────────────────────────────────────────────────────────
# BASE PER RUOLO
# ───────────────────────────────────────────────────────────────
BASE_RUOLO: dict[str, float] = {
    "POR": 0.85,
    "DIF": 0.90,
    "CC":  1.05,
    "ATT": 1.20,
}

# ───────────────────────────────────────────────────────────────
# FATTORE ETÀ — campana, picco 24-27
# ───────────────────────────────────────────────────────────────
def fattore_eta(eta: int) -> float:
    if eta is None or eta <= 0:
        return 1.0
    if eta <= 21:
        return 1.05  # under-21 alto potenziale
    if 22 <= eta <= 23:
        return 1.10
    if 24 <= eta <= 27:
        return 1.15
    if 28 <= eta <= 29:
        return 1.05
    if eta == 30:
        return 1.00
    if 31 <= eta <= 33:
        return 0.85
    if eta == 34:
        return 0.70
    return 0.55  # >=35


# ───────────────────────────────────────────────────────────────
# FATTORE MINUTAGGIO — 0.6 a 1.0
# ───────────────────────────────────────────────────────────────
def fattore_minutaggio(pct: float) -> float:
    if pct is None or pct < 0:
        return 0.6
    if pct >= 1.0:
        return 1.0
    if pct < 0.3:
        return 0.6
    # lineare tra 0.3 e 1.0
    return 0.6 + (pct - 0.3) * (1.0 - 0.6) / (1.0 - 0.3)


# ───────────────────────────────────────────────────────────────
# FATTORE SQUADRA — placeholder Fase 1, calibrazione in Fase 2
# (top tier = 1.20, mid = 1.0, bassa = 0.90)
# ───────────────────────────────────────────────────────────────
DEFAULT_FATTORE_SQUADRA: float = 1.00

# ───────────────────────────────────────────────────────────────
# K — scala globale (calibrata in Fase 2 per banda prezzo target)
# In Fase 1 K = 1.0 → valore iniziale ≈ VALORE_BASE_GIOCATORE_CREDITI per ruoli/tutto medio
# ───────────────────────────────────────────────────────────────
K_GLOBAL: float = 1.0

# Score performance placeholder (default 1.0 = neutro)
# In Fase 2: calcolato da statistiche stagione precedente
DEFAULT_SCORE_PERFORMANCE: float = 1.0
