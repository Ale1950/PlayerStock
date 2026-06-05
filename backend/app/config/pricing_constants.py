"""
PlayerStock — Pricing & economy constants (Fase 1 = placeholder).

⚠️ I valori esatti dei driver di pricing (gol/assist/voto/minuti/clamp) sono
estratti da `Gioco 5.xls` foglio "Serie 1" IN FASE 2 (Claude Code).
Qui in Fase 1 servono SOLO i parametri di struttura azionaria ed economia,
che sono già "Decisioni Finali" (PROJECT_SPEC.md §2).

DO NOT EDIT manually without updating PROJECT_SPEC.md and DECISIONS.md.
"""
from __future__ import annotations

# ───────────────────────────────────────────────────────────────
# STRUTTURA AZIONARIA — DECISIONI FINALI PROJECT_SPEC.md §2
# ───────────────────────────────────────────────────────────────
FLOAT_AZIONI_PER_GIOCATORE: int = 1_000_000
VALORE_BASE_GIOCATORE_CREDITI: float = 10_000.0
PREZZO_BASE_AZIONE_CREDITI: float = 0.01  # = VALORE_BASE / FLOAT
CAP_UTENTE_PCT: float = 0.03  # 3%
CAP_UTENTE_AZIONI: int = 30_000
HOLDING_MINIMO_GIORNI: int = 7
FLOOR_PCT_PREZZO_INIZIALE: float = 0.10
DISPLAY_DECIMALS: int = 4

# ───────────────────────────────────────────────────────────────
# ECONOMIA CREDITI
# ───────────────────────────────────────────────────────────────
BUDGET_INIZIALE_UTENTE_CREDITI: float = 10_000.0
FEE_MARKETPLACE_TOTALE_PCT: float = 0.07
FEE_BUYER_PCT: float = 0.035
FEE_SELLER_PCT: float = 0.035
CREDITI_TO_EUR_RATE: float = 1.0  # fittizio, NON convertibile

# ───────────────────────────────────────────────────────────────
# PRICING DRIVER — TODO Fase 2 (Claude Code estrae da Gioco 5.xls)
# ───────────────────────────────────────────────────────────────

# TODO Fase 2: ESTRARRE DA Gioco 5.xls foglio "Serie 1"
MINUTI_GIOCATI: dict[str, dict[str, float]] = {
    "DIF": {"GT_60": 0.0028, "BETWEEN_45_60": -0.0025, "LE_45": -0.0050},
    "CC":  {"GT_60": 0.0038, "BETWEEN_45_60": -0.0015, "LE_45": -0.0038},
    "ATT": {"GT_60": 0.0045, "BETWEEN_45_60": 0.0,     "LE_45": -0.0010},
    "POR": {"GT_60": 0.0018, "BETWEEN_45_60": -0.0025, "LE_45": -0.0050},
}

# TODO Fase 2: completare driver gol, gol_subiti, espulsione, assist, rigori, voto, autorete, ammonizione

# Range clamp giornaliero (DECISIONI FINALI)
RANGE_CLAMP: dict[str, dict[str, float]] = {
    "DIF": {"up": 0.0413, "down": -0.0254},
    "CC":  {"up": 0.0310, "down": -0.0212},
    "ATT": {"up": 0.0287, "down": -0.0281},
    "POR": {"up": 0.0424, "down": -0.0370},
}

# Driver di mercato (su order flow REALE)
MARKET_DRIVERS: dict[str, float] = {
    "buy_1_5": 0.012, "buy_6_20": 0.020, "buy_over_20": 0.025,
    "sell_1_5": -0.012, "sell_6_20": -0.020, "sell_over_20": -0.025,
}

# Driver engagement
ENGAGEMENT_DRIVERS: dict[str, float] = {
    "training_2_week": 0.0025, "training_3_4_week": 0.0040, "training_5plus_week": 0.0048,
    "league_1_5": 0.0025, "league_6_20": 0.0055, "league_over_20": 0.0071,
}
