"""Valore di mercato €M — LAYER DI DISPLAY (Fase 2c). Economia di trading INTATTA.

I 400 giocatori sono FITTIZI: qui si genera un `market_value_eur` realistico per
FORMA e SCALA (poche stelle costose, lunga coda di gregari), stile Transfermarkt,
**senza dati esterni** e in modo **deterministico/riproducibile**.

Modello (Opzione B):
  - Rosa strutturata per squadra: fasce S/A/B/C/D con conteggi ~1/3/6/6/4 su 20,
    assegnate per RANK del talento = `score_performance` (lo STESSO che guida il prezzo).
  - Ogni fascia ha un range €; posizione entro fascia = score (più alto → più in alto).
  - Livello squadra (grande/media/piccola, da `fattore_squadra`) = moltiplicatore =
    UNICO scostamento voluto (premio club): a parità di rank, big > piccola.

Il valore mostrato in UI SEGUE il prezzo via àncora fissata al seed:
    valore_mostrato = prezzo_corrente × anchor,  anchor = seed / prezzo_iniziale
così il movimento giornaliero è proporzionale e la coda pesante del seed resta.

⚠️ Solo strato di visualizzazione: NON tocca prezzo quota, budget, cap, fee, pricing.
TUTTA la calibrazione è in MARKET_VALUE_CONFIG (un solo punto, facile da ritarare).
"""
from __future__ import annotations

from app.config.pricing_constants import FLOAT_AZIONI_PER_GIOCATORE

# ────────────────────────── CALIBRAZIONE (unico punto) ──────────────────────────
# Ritarabile dopo aver visto la distribuzione reale del seed.
MARKET_VALUE_CONFIG: dict = {
    # fasce della rosa (conteggi su rosa-tipo da 20; scalati per rose diverse)
    "fascia_counts": [("S", 1), ("A", 3), ("B", 6), ("C", 6), ("D", 4)],
    # range €/fascia (coda pesante: stelle in alto, gregari in basso)
    "fascia_range_eur": {
        "S": (58_000_000.0, 108_000_000.0),
        "A": (22_000_000.0, 52_000_000.0),
        "B": (7_000_000.0, 22_000_000.0),
        "C": (2_000_000.0, 7_000_000.0),
        "D": (600_000.0, 2_000_000.0),
    },
    # premio club (UNICO scostamento dal rank-talento)
    "club_mult": {"grande": 1.00, "media": 0.80, "piccola": 0.62},
    # esponente coda: shaping della posizione entro fascia (1.0 = lineare)
    "tail_gamma": 1.0,
    # clamp globale di sicurezza
    "global_clamp_eur": (500_000.0, 115_000_000.0),
}


def level_from_fattore_squadra(fattore: float) -> str:
    """Livello squadra dal fattore_squadra sintetico (1.25 top / 1.00 mid / 0.93 weak)."""
    if fattore >= 1.15:
        return "grande"
    if fattore <= 0.96:
        return "piccola"
    return "media"


def _fascia_sequence(n: int) -> list[str]:
    """Sequenza di fasce (lunghezza n) in ordine S→D, conteggi scalati alla rosa."""
    counts = MARKET_VALUE_CONFIG["fascia_counts"]
    total = sum(c for _, c in counts)
    seq: list[str] = []
    assigned = 0
    for idx, (label, c) in enumerate(counts):
        k = (n - assigned) if idx == len(counts) - 1 else round(c * n / total)
        k = max(0, min(k, n - assigned))
        seq.extend([label] * k)
        assigned += k
    # pad/truncate di sicurezza
    if len(seq) < n:
        seq.extend([counts[-1][0]] * (n - len(seq)))
    return seq[:n]


def assign_team_market_values(players: list[dict]) -> dict[str, float]:
    """Assegna market_value_eur (seed) ai giocatori di UNA squadra.

    players: lista di dict con 'key', 'score', 'fattore_squadra'.
    Ritorna {key: valore_eur}. Deterministico (tie-break su key).
    """
    cfg = MARKET_VALUE_CONFIG
    ranges = cfg["fascia_range_eur"]
    club_mult = cfg["club_mult"]
    gamma = cfg["tail_gamma"]
    gmin, gmax = cfg["global_clamp_eur"]

    # rank-talento = score (desc), tie-break deterministico su key
    ranked = sorted(players, key=lambda p: (-float(p["score"]), str(p["key"])))
    fasce = _fascia_sequence(len(ranked))

    # raggruppa i giocatori per fascia, mantenendo l'ordine (score desc)
    groups: dict[str, list[dict]] = {}
    for p, f in zip(ranked, fasce):
        groups.setdefault(f, []).append(p)

    out: dict[str, float] = {}
    for label, members in groups.items():
        lo, hi = ranges[label]
        m = len(members)
        for idx, p in enumerate(members):  # idx 0 = score più alto della fascia
            pos = 1.0 - (idx + 0.5) / m            # alto della fascia → ~1, basso → ~0
            base = lo + (hi - lo) * (pos ** gamma)
            level = level_from_fattore_squadra(float(p["fattore_squadra"]))
            val = base * club_mult[level]
            out[str(p["key"])] = max(gmin, min(gmax, val))
    return out


def price_from_market_value(market_value_eur: float,
                            float_quote: int = FLOAT_AZIONI_PER_GIOCATORE) -> float:
    """Prezzo quota €  = valore di mercato € / FLOAT  (migrazione € D7, unica fonte)."""
    if not float_quote:
        return 0.0
    return market_value_eur / float_quote


def market_value_eur_from_price(prezzo_eur: float,
                                float_quote: int = FLOAT_AZIONI_PER_GIOCATORE) -> float:
    """Valore di mercato € mostrato = prezzo quota × FLOAT (segue il prezzo, live)."""
    return prezzo_eur * float_quote
