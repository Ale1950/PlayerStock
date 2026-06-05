"""
PlayerStock — Valuation constants (Fase 2, calibrate da Claude Code).

Formula (PROJECT_SPEC.md §5):
    ValoreIniziale = K_GLOBAL × BASE_RUOLO[r] × f_score × f_età × f_minutaggio × f_squadra
    prezzo_iniziale = ValoreIniziale / FLOAT_AZIONI_PER_GIOCATORE

CALIBRAZIONE K_GLOBAL + banda prezzo (decisa nel progetto):
  - neutro (score 1.0, età picco, minutaggio pieno, squadra media) ⇒ valore ≈ 10.000 ⇒ prezzo ≈ 0.01;
  - banda prezzo target: top 0.035–0.050, medi 0.010–0.020, riserve 0.005–0.010;
  - VINCOLO DURO: gli estremi devono cadere DENTRO ~0.005–0.050.

Poiché i fattori sono MOLTIPLICATIVI, lo spread naturale (range pieni) sfora il floor 0.005
verso il basso. Per rispettare il vincolo i range dei fattori sono stati COMPRESSI (vedi sotto).
Esito documentato (estremi calcolati, vedi tests/test_valuation_engine.py):
  - min  (POR, score≤0.80, età≥35, minutaggio basso, squadra debole) ≈ 5.071 cr  ⇒ prezzo ≈ 0.00507
  - max  (ATT, score 2.0, età picco, minutaggio pieno, squadra top)   ≈ 26.880 cr ⇒ prezzo ≈ 0.02688
Entrambi ⊂ [0.005, 0.050] ✓. NOTA: il top naturale si ferma ~0.027 (fascia medio-alta): per
toccare 0.035–0.050 servirebbe allargare score/squadra, ma ciò sfonderebbe il floor 0.005 →
priorità al vincolo duro. Da rivedere col fondatore se si vuole un top più alto.
"""
from __future__ import annotations

# ───────────────────────────────────────────────────────────────
# K globale: neutro (tutti i fattori = 1.0, base media = 1.0) ⇒ 10.000 cr
# ───────────────────────────────────────────────────────────────
K_GLOBAL: float = 10_000.0

# ───────────────────────────────────────────────────────────────
# BASE PER RUOLO (relativa, media = 1.0 → il neutro medio vale K_GLOBAL)
# (0.88 + 0.95 + 1.05 + 1.12) / 4 = 1.0
# ───────────────────────────────────────────────────────────────
BASE_RUOLO: dict[str, float] = {
    "POR": 0.88,
    "DIF": 0.95,
    "CC":  1.05,
    "ATT": 1.12,
}

# ───────────────────────────────────────────────────────────────
# SCORE PERFORMANCE: input atteso 0.5–2.0 (1.0 = neutro). Compresso al floor
# a 0.80 in valuation per non sfondare la banda prezzo verso il basso.
# ───────────────────────────────────────────────────────────────
SCORE_MIN: float = 0.80
SCORE_MAX: float = 2.00
DEFAULT_SCORE_PERFORMANCE: float = 1.0


def fattore_score(score: float) -> float:
    if score is None:
        return 1.0
    return max(SCORE_MIN, min(SCORE_MAX, score))


# ───────────────────────────────────────────────────────────────
# FATTORE ETÀ — campana COMPRESSA, picco 24–27 = 1.0, minimo 0.87 (>=35)
# ───────────────────────────────────────────────────────────────
def fattore_eta(eta: int | None) -> float:
    if eta is None or eta <= 0:
        return 1.0
    if eta <= 21:
        return 0.93
    if eta <= 23:
        return 0.96
    if eta <= 27:
        return 1.00  # picco
    if eta <= 29:
        return 0.96
    if eta == 30:
        return 0.93
    if eta <= 33:
        return 0.90
    if eta == 34:
        return 0.88
    return 0.87  # >=35


# ───────────────────────────────────────────────────────────────
# FATTORE MINUTAGGIO — COMPRESSO a [0.90, 1.0] (1.0 = titolare fisso)
# ───────────────────────────────────────────────────────────────
MINUTAGGIO_MIN: float = 0.90


def fattore_minutaggio(pct: float | None) -> float:
    if pct is None or pct < 0:
        return MINUTAGGIO_MIN
    if pct >= 1.0:
        return 1.0
    if pct <= 0.3:
        return MINUTAGGIO_MIN
    # lineare tra 0.3 (→0.90) e 1.0 (→1.0)
    return MINUTAGGIO_MIN + (pct - 0.3) * (1.0 - MINUTAGGIO_MIN) / (1.0 - 0.3)


# ───────────────────────────────────────────────────────────────
# FATTORE SQUADRA — banda COMPRESSA [0.92, 1.20], media = 1.0
# (calibrazione fine dei singoli club in fase dati reali)
# ───────────────────────────────────────────────────────────────
SQUADRA_MIN: float = 0.92
SQUADRA_MAX: float = 1.20
DEFAULT_FATTORE_SQUADRA: float = 1.00


def clamp_fattore_squadra(f: float) -> float:
    return max(SQUADRA_MIN, min(SQUADRA_MAX, f))


# Banda prezzo decisa (per documentazione/validazione)
PRICE_BAND_MIN: float = 0.005
PRICE_BAND_MAX: float = 0.050
