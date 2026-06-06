"""RED→GREEN: market_value_eur — layer di realismo €M (display), economia INTATTA.

Generazione Opzione B: rosa strutturata per-squadra (fasce 1/3/6/6/4) + livello
squadra (grande/media/piccola) come UNICO scostamento (premio club). Valore assegnato
sul rank-talento = score_performance (lo stesso che guida il prezzo).

Test (vedi chiarimenti utente):
- NO monotonìa stretta cross-giocatore (il premio club la rompe apposta).
- SÌ Spearman(valore, talento) alto + effetto club (a parità di rank, big > piccola).
- SÌ tracking per-giocatore: valore = prezzo_corrente × anchor; +10% prezzo → +10% valore.
- SÌ regressione: backfill tocca solo {market_value_eur_seed, mv_anchor_eur, updated_at}.
"""
from __future__ import annotations

import pytest

from app.valuation.market_value import (
    MARKET_VALUE_CONFIG,
    assign_team_market_values,
    level_from_fattore_squadra,
    market_value_eur_from_price,
    price_from_market_value,
)
from app.valuation.synthetic_score import synthetic_score, synthetic_team_tier


# ───────────────────── helpers ─────────────────────
ROLES = ["POR", "DIF", "CC", "ATT"]


def _synthetic_league(n_teams: int = 20, per_team: int = 20) -> list[dict]:
    """Lega sintetica deterministica: n_teams squadre × per_team giocatori.

    Riusa gli stessi score/tier sintetici del seed reale → distribuzione realistica.
    Ritorna la lista piatta con 'team' per raggruppare.
    """
    league: list[dict] = []
    for t in range(n_teams):
        team_id = f"team-{t}"
        fattore = synthetic_team_tier(team_id)
        for i in range(per_team):
            role = ROLES[i % 4]
            ext = f"{team_id}-p{i}"
            league.append({
                "key": ext,
                "team": team_id,
                "score": synthetic_score(role, ext),
                "fattore_squadra": fattore,
            })
    return league


def _values_by_team(league: list[dict]) -> dict[str, float]:
    """Raggruppa per squadra, assegna i valori, ritorna {key: valore_eur}."""
    by_team: dict[str, list[dict]] = {}
    for p in league:
        by_team.setdefault(p["team"], []).append(p)
    out: dict[str, float] = {}
    for players in by_team.values():
        out.update(assign_team_market_values(players))
    return out


def _spearman(xs: list[float], ys: list[float]) -> float:
    def ranks(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sx = sum((a - mx) ** 2 for a in rx) ** 0.5
    sy = sum((b - my) ** 2 for b in ry) ** 0.5
    return cov / (sx * sy) if sx and sy else 0.0


# ───────────────────── distribuzione ─────────────────────
def test_heavy_tail_spread_and_shape():
    """Coda pesante: pochi alti, molti bassi, spread realistico 150–250x."""
    league = _synthetic_league()
    vals = sorted(_values_by_team(league).values())
    n = len(vals)
    assert n == 400
    spread = vals[-1] / vals[0]
    assert 150 <= spread <= 250, f"spread {spread:.0f}x fuori [150,250]"
    median = vals[n // 2]
    assert 4e6 <= median <= 14e6, f"mediana €{median/1e6:.1f}M fuori [4,14]M"
    # pochi elite
    assert sum(v > 60e6 for v in vals) <= 0.08 * n
    # coda pesante: molti più economici che costosi
    assert sum(v < 5e6 for v in vals) >= sum(v > 20e6 for v in vals)


def test_value_range_within_targets():
    """Estremi entro la scala Transfermarkt-like fittizia."""
    vals = list(_values_by_team(_synthetic_league()).values())
    assert min(vals) >= 0.4e6
    assert max(vals) <= 125e6
    assert max(vals) >= 60e6  # esistono fuoriclasse


# ───────────────────── correlazione talento + club ─────────────────────
def test_spearman_value_vs_talent_high():
    """Valore fortemente correlato col talento (score) — quasi monotòno."""
    league = _synthetic_league()
    vals = _values_by_team(league)
    xs = [p["score"] for p in league]
    ys = [vals[p["key"]] for p in league]
    assert _spearman(xs, ys) >= 0.80


def test_club_premium_same_rank_big_gt_small():
    """A parità di rank-talento, squadra grande > piccola (unico scostamento voluto)."""
    scores = [2.0, 1.6, 1.4, 1.2, 1.1, 1.05, 1.0, 0.95, 0.9, 0.88,
              0.85, 0.83, 0.8, 0.78, 0.76, 0.74, 0.72, 0.7, 0.65, 0.6]
    big = [{"key": f"b{i}", "score": s, "fattore_squadra": 1.25} for i, s in enumerate(scores)]
    small = [{"key": f"s{i}", "score": s, "fattore_squadra": 0.93} for i, s in enumerate(scores)]
    assert level_from_fattore_squadra(1.25) == "grande"
    assert level_from_fattore_squadra(0.93) == "piccola"
    vb = assign_team_market_values(big)
    vs = assign_team_market_values(small)
    for i in range(len(scores)):
        assert vb[f"b{i}"] > vs[f"s{i}"], f"rank {i}: big non > piccola"


# ───────────────────── determinismo ─────────────────────
def test_deterministic_reproducible():
    league = _synthetic_league()
    a = _values_by_team(league)
    b = _values_by_team(league)
    assert a == b


# ───────────────────── prezzo ↔ valore (D7: una sola scala) ─────────────────────
def test_price_value_roundtrip():
    """value = price × FLOAT e price = value / FLOAT (range € atteso)."""
    seed = 72_500_000.0
    price = price_from_market_value(seed)          # /1M
    assert price == pytest.approx(72.5)            # €72,50
    assert market_value_eur_from_price(price) == pytest.approx(seed)
    # +10% prezzo → +10% valore
    assert market_value_eur_from_price(price * 1.1) == pytest.approx(seed * 1.1)


def test_config_single_calibration_point():
    """Tutti i parametri di taratura in un solo posto, facili da cambiare."""
    for k in ("fascia_counts", "fascia_range_eur", "club_mult", "tail_gamma", "global_clamp_eur"):
        assert k in MARKET_VALUE_CONFIG


# ───────────────────── REGRESSIONE: ancora € + economia intatta ─────────────────────
@pytest.mark.asyncio
async def test_backfill_sets_euro_anchor_and_keeps_pool(mock_db):
    """Backfill setta seed €M + prezzo € (= seed/FLOAT); float/pool NON cambiano."""
    from app.cli.backfill_market_value import backfill_market_values

    team_id = "t1"
    base = {
        "sport_id": "calcio", "status": "ACTIVE", "team_fantasy_id": team_id,
        "role": "ATT", "float_quote": 1_000_000, "primary_pool_qty": 1_000_000,
        "circulating_qty": 0,
    }
    docs = []
    for i in range(20):
        score = 2.0 - i * 0.07
        docs.append({**base, "internal_full_name": f"P{i}", "source_external_id": f"e{i}",
                     "score_performance": score, "fattore_squadra": 1.25,
                     "valore_iniziale_eur": 5.0, "prezzo_iniziale_eur": 5.0,
                     "prezzo_corrente_eur": 5.0})
    await mock_db.athletes.insert_many(docs)

    n = await backfill_market_values(mock_db)
    assert n == 20

    after = await mock_db.athletes.find({}).to_list(length=100)
    for d in after:
        # float/pool invariati (non è un trade)
        assert d["float_quote"] == 1_000_000
        assert d["primary_pool_qty"] == 1_000_000
        # ancora € coerente: prezzo = seed / FLOAT, value = prezzo × FLOAT
        seed = d["market_value_eur_seed"]
        assert seed > 0
        assert d["prezzo_iniziale_eur"] == pytest.approx(seed / 1_000_000)
        assert d["prezzo_equo_eur"] == pytest.approx(d["prezzo_iniziale_eur"])
        assert d["prezzo_corrente_eur"] == pytest.approx(d["prezzo_iniziale_eur"])
        assert d["valore_iniziale_eur"] == pytest.approx(seed)
        # prezzo nel range € atteso
        assert 0.4 <= d["prezzo_iniziale_eur"] <= 120.0


@pytest.mark.asyncio
async def test_backfill_idempotent(mock_db):
    from app.cli.backfill_market_value import backfill_market_values
    docs = [{"sport_id": "calcio", "status": "ACTIVE", "team_fantasy_id": "t1", "role": "CC",
             "source_external_id": f"e{i}", "internal_full_name": f"P{i}",
             "score_performance": 1.5 - i * 0.1, "fattore_squadra": 1.0,
             "float_quote": 1_000_000, "valore_iniziale_eur": 10000.0,
             "prezzo_iniziale_eur": 0.01, "prezzo_corrente_eur": 0.01}
            for i in range(6)]
    await mock_db.athletes.insert_many(docs)
    await backfill_market_values(mock_db)
    first = {d["source_external_id"]: d["market_value_eur_seed"]
             for d in await mock_db.athletes.find({}).to_list(length=10)}
    await backfill_market_values(mock_db)
    second = {d["source_external_id"]: d["market_value_eur_seed"]
              for d in await mock_db.athletes.find({}).to_list(length=10)}
    assert first == second
