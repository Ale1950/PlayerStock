# Pricing & Valuation Model — PlayerStock

Riferimento di dettaglio. Spec autorevole: `PROJECT_SPEC.md` §5–6. Valori esatti dei driver
**da estrarre da `Gioco 5.xls` foglio "Serie 1" in Fase 2** (Claude Code).

---

## 1. Valutazione iniziale (`valuation_constants.py`)

```
ValoreIniziale = BaseRuolo × ScorePerformance × FattoreEtà × FattoreMinutaggio × FattoreSquadra × K
```

| Fattore | Definizione |
|---|---|
| BaseRuolo | POR 0.85 · DIF 0.90 · CC 1.05 · ATT 1.20 |
| ScorePerformance | output 12 mesi normalizzato per ruolo ~1.0 (range 0.5–2.0) |
| FattoreEtà | campana, picco 24–27 (1.15@24 · 1.0@30 · 0.7@34 · under-21 alto pot. 1.05) |
| FattoreMinutaggio | % minuti → 0.6–1.0 |
| FattoreSquadra | 0.9–1.2 |
| K | scala globale (taratura) |

**Struttura azionaria** (DECISIONI FINALI): float **1.000.000** quote/giocatore; prezzo iniziale
**0.01 Credito** (= valore base 10.000 / 1.000.000); cap utente **3%** (30.000 quote).

---

## 2. Pricing engine (`pricing_constants.py`)

```python
def update_price(old_price, perf_pct, market_pct, eng_pct, ruolo, initial_price):
    delta = perf_pct + market_pct + eng_pct
    delta = clamp(delta, RANGE_CLAMP[ruolo]["down"], RANGE_CLAMP[ruolo]["up"])
    new_price = old_price * (1 + delta)
    return max(new_price, initial_price * FLOOR_PCT_PREZZO_INIZIALE)  # floor 10%
```

### Costanti note (da consolidare/verificare con `Gioco 5.xls` in Fase 2)

```python
# Struttura azionaria
FLOAT_AZIONI_PER_GIOCATORE = 1_000_000
VALORE_BASE_GIOCATORE_CREDITI = 10_000
PREZZO_BASE_AZIONE_CREDITI = 0.01
CAP_UTENTE_PCT = 0.03
CAP_UTENTE_AZIONI = 30_000
HOLDING_MINIMO_GIORNI = 7
FLOOR_PCT_PREZZO_INIZIALE = 0.10
DISPLAY_DECIMALS = 4

# Economia
BUDGET_INIZIALE_UTENTE = 10_000
FEE_MARKETPLACE_TOTALE_PCT = 0.07
FEE_BUYER_PCT = 0.035
FEE_SELLER_PCT = 0.035
CREDITI_TO_EUR_RATE = 1.0   # 1 Credito = €1 fittizio, NON convertibile

# Valuation
BASE_RUOLO = {"POR": 0.85, "DIF": 0.90, "CC": 1.05, "ATT": 1.20}

# Driver minuti giocati (frazioni)
MINUTI_GIOCATI = {
    "DIF": {"GT_60": 0.0028, "BETWEEN_45_60": -0.0025, "LE_45": -0.005},
    "CC":  {"GT_60": 0.0038, "BETWEEN_45_60": -0.0015, "LE_45": -0.0038},
    "ATT": {"GT_60": 0.0045, "BETWEEN_45_60": 0.0,      "LE_45": -0.001},
    "POR": {"GT_60": 0.0018, "BETWEEN_45_60": -0.0025, "LE_45": -0.005},
}
# TODO Fase 2: gol fatti/subiti, espulsione, assist, rigori, voto, autorete,
#              ammonizione — valori esatti da Gioco 5.xls foglio "Serie 1".

# Clamp giornaliero per ruolo
RANGE_CLAMP = {
    "DIF": {"up": 0.0413, "down": -0.0254},
    "CC":  {"up": 0.0310, "down": -0.0212},
    "ATT": {"up": 0.0287, "down": -0.0281},
    "POR": {"up": 0.0424, "down": -0.0370},
}

# Driver mercato (order flow REALE)
MARKET_DRIVERS = {
    "buy_1_5": 0.012,   "buy_6_20": 0.020,   "buy_over_20": 0.025,
    "sell_1_5": -0.012, "sell_6_20": -0.020, "sell_over_20": -0.025,
}

# Driver engagement
ENGAGEMENT_DRIVERS = {
    "training_2_week": 0.0025, "training_3_4_week": 0.0040, "training_5plus_week": 0.0048,
    "league_1_5": 0.0025,      "league_6_20": 0.0055,        "league_over_20": 0.0071,
}
```

---

## 3. Testing previsto (Fase 2–3)

- **Valuation**: fixture per ruolo/età/minutaggio → valore atteso entro tolleranza.
- **Pricing**: ogni driver in isolamento + combinato; clamp ai range; floor al 10%.
- **Order book** (Fase 3): matching, fee 7% (3.5+3.5), holding 7gg, cap 3%, quantità reali.
- Eseguibili con `pytest` (un singolo comando).
