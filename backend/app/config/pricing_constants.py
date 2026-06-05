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
# PRICING DRIVER — Fase 2: estratti da `Gioco 5.xls` foglio "Serie 1".
# Sorgente di verità: lo strumento `tools/extract_gioco5.py` rilegge l'xls;
# `tests/test_gioco5_golden.py` garantisce che questi valori restino allineati.
# Coefficienti = variazione % settimanale per evento, per ruolo e banda.
# DO NOT EDIT a mano: rigenerare con extract_gioco5 + golden test.
# ───────────────────────────────────────────────────────────────
DRIVERS: dict[str, dict[str, dict[str, float]]] = {
    "MINUTI_GIOCATI": {
        "DIF": {"GT_60": 0.0028, "BETWEEN_45_60": -0.0025, "LE_45": -0.005},
        "CC":  {"GT_60": 0.0038, "BETWEEN_45_60": -0.0015, "LE_45": -0.0038},
        "ATT": {"GT_60": 0.0045, "BETWEEN_45_60": 0.0,     "LE_45": -0.001},
        "POR": {"GT_60": 0.0018, "BETWEEN_45_60": -0.0025, "LE_45": -0.005},
    },
    "GOL_FATTI": {
        "DIF": {"ONE": 0.0045, "GE_2": 0.0075, "ZERO": 0.0},
        "CC":  {"ONE": 0.0028, "GE_2": 0.0045, "ZERO": 0.0},
        "ATT": {"ONE": 0.0018, "GE_2": 0.0025, "ZERO": -0.0025},
        "POR": {"ONE": 0.006,  "GE_2": 0.0089, "ZERO": 0.0},
    },
    "GOL_SUBITI": {
        "DIF": {"ONE": -0.0035, "GE_2": -0.005,  "ZERO": 0.0018},
        "CC":  {"ONE": -0.0025, "GE_2": -0.004,  "ZERO": 0.001},
        "ATT": {"ONE": -0.0015, "GE_2": -0.0025, "ZERO": 0.0005},
        "POR": {"ONE": -0.0035, "GE_2": -0.0065, "ZERO": 0.0025},
    },
    "AMMONIZIONE": {
        "DIF": {"ONE": -0.0025, "TWO": -0.0038, "ZERO": 0.0038},
        "CC":  {"ONE": -0.0025, "TWO": -0.0038, "ZERO": 0.0038},
        "ATT": {"ONE": -0.0035, "TWO": -0.0045, "ZERO": 0.0038},
        "POR": {"ONE": -0.0025, "TWO": -0.0038, "ZERO": 0.0038},
    },
    "ESPULSIONE": {
        "DIF": {"ONE": -0.0038},
        "CC":  {"ONE": -0.005},
        "ATT": {"ONE": -0.0075},
        "POR": {"ONE": -0.0089},
    },
    "ASSIST": {
        "DIF": {"ONE": 0.0045, "GE_2": 0.0065, "ZERO": 0.0},
        "CC":  {"ONE": 0.0015, "GE_2": 0.0025, "ZERO": -0.0018},
        "ATT": {"ONE": 0.001,  "GE_2": 0.0015, "ZERO": -0.0023},
        "POR": {"ONE": 0.0045, "GE_2": 0.0065, "ZERO": 0.0},
    },
    "RIGORI_SEGNATI": {
        "DIF": {"ONE": 0.005, "TWO": 0.0075, "THREE": 0.0089},
        "CC":  {"ONE": 0.005, "TWO": 0.0075, "THREE": 0.0089},
        "ATT": {"ONE": 0.005, "TWO": 0.0075, "THREE": 0.0089},
        "POR": {"ONE": 0.005, "TWO": 0.0075, "THREE": 0.0089},
    },
    "RIGORI_SBAGLIATI": {
        "DIF": {"ONE": -0.005, "GE_2": -0.0089, "ZERO": 0.0},
        "CC":  {"ONE": -0.005, "GE_2": -0.0089, "ZERO": 0.0},
        "ATT": {"ONE": -0.005, "GE_2": -0.0089, "ZERO": 0.0},
        "POR": {"ONE": -0.005, "GE_2": -0.0089, "ZERO": 0.0},
    },
    "RIGORI_PARATI": {
        "DIF": {"ONE": 0.005, "TWO": 0.0089, "THREE": 0.015},
        "CC":  {"ONE": 0.005, "TWO": 0.0089, "THREE": 0.015},
        "ATT": {"ONE": 0.005, "TWO": 0.0089, "THREE": 0.015},
        "POR": {"ONE": 0.005, "TWO": 0.0078, "THREE": 0.01},
    },
    "VOTO_PORTIERE": {
        "DIF": {"LT_6": 0.0, "B6_7": 0.0, "GE_8": 0.0},
        "CC":  {"LT_6": 0.0, "B6_7": 0.0, "GE_8": 0.0},
        "ATT": {"LT_6": 0.0, "B6_7": 0.0, "GE_8": 0.0},
        "POR": {"LT_6": -0.005, "B6_7": 0.0038, "GE_8": 0.005},
    },
    "AUTORETE": {
        "DIF": {"ONE": -0.005, "TWO": -0.0075, "GE_3": -0.0089},
        "CC":  {"ONE": -0.005, "TWO": -0.0075, "GE_3": -0.0089},
        "ATT": {"ONE": -0.005, "TWO": -0.0075, "GE_3": -0.0089},
        "POR": {"ONE": -0.005, "TWO": -0.0075, "GE_3": -0.0089},
    },
}

# Alias retro-compat (usato in Fase 1 seed). = DRIVERS["MINUTI_GIOCATI"]
MINUTI_GIOCATI: dict[str, dict[str, float]] = DRIVERS["MINUTI_GIOCATI"]

# Range clamp settimanale per ruolo (Gioco 5.xls "Serie 1" righe Max/Min)
RANGE_CLAMP: dict[str, dict[str, float]] = {
    "DIF": {"up": 0.0413, "down": -0.0254},
    "CC":  {"up": 0.031,  "down": -0.0212},
    "ATT": {"up": 0.0287, "down": -0.0281},
    "POR": {"up": 0.0424, "down": -0.037},
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
