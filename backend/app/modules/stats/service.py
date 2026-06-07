"""Backbone dati — aggregati INTERNI (giocatori fittizi, nessun web).

Tre famiglie: market-wide, per-giocatore, per-utente. Volume e n° possessori
derivano dagli ordini/holdings (già tracciati). Funzioni pure separate dalle
funzioni DB-backed (TDD).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence

from app.config.valuation_constants import (
    BASE_RUOLO,
    K_GLOBAL,
    clamp_fattore_squadra,
    fattore_eta,
    fattore_minutaggio,
    fattore_score,
)
from app.models.common import utc_now
from app.modules.portfolio.service import build_portfolio_response
from app.valuation.synthetic_stats import synthetic_weekly_stats


# ───────────────────────── PURE ─────────────────────────
def pct_change(old: float, new: float) -> float | None:
    if not old:
        return None
    return (new - old) / old * 100.0


def summarize(values: Sequence[float]) -> dict:
    vals = list(values)
    if not vals:
        return {"count": 0, "min": 0.0, "max": 0.0, "avg": 0.0}
    return {"count": len(vals), "min": min(vals), "max": max(vals), "avg": sum(vals) / len(vals)}


def price_distribution_by(athletes: Sequence[dict], key: str) -> dict[str, dict]:
    groups: dict[str, list[float]] = {}
    for a in athletes:
        groups.setdefault(str(a.get(key)), []).append(float(a.get("prezzo_corrente_eur", 0.0)))
    return {k: summarize(v) for k, v in groups.items()}


def top_movers(rows: Sequence[dict], n: int = 5) -> dict:
    valid = [r for r in rows if r.get("var_pct") is not None]
    asc = sorted(valid, key=lambda r: r["var_pct"])
    desc = sorted(valid, key=lambda r: r["var_pct"], reverse=True)
    return {"gainers": desc[:n], "losers": asc[:n]}


def decompose_value(athlete: dict) -> dict:
    role = athlete["role"]
    score = float(athlete.get("score_performance", 1.0))
    eta = athlete.get("age")
    minut = float(athlete.get("minutaggio_pct", 1.0))
    fsq = float(athlete.get("fattore_squadra", 1.0))
    return {
        "k_global": K_GLOBAL,
        "base_ruolo": BASE_RUOLO[role],
        "f_score": fattore_score(score),
        "f_eta": fattore_eta(eta),
        "f_minutaggio": fattore_minutaggio(minut),
        "f_squadra": clamp_fattore_squadra(fsq),
        # D7: valore equo = ancora € × FLOAT (i fattori sopra restano audit sintetico del rank).
        "valore_equo": float(athlete.get("prezzo_equo_eur")
                             or athlete.get("prezzo_corrente_eur") or 0.0)
        * float(athlete.get("float_quote") or 1_000_000),
    }


def allocation_by(positions: Sequence[dict], key: str) -> list[dict]:
    by: dict[str, float] = {}
    for p in positions:
        by[str(p.get(key))] = by.get(str(p.get(key)), 0.0) + float(p.get("current_value", 0.0))
    total = sum(by.values()) or 1.0
    out = [{"key": k, "value": v, "pct": v / total * 100.0} for k, v in by.items()]
    out.sort(key=lambda x: x["value"], reverse=True)
    return out


def realized_pnl_from_orders(orders: Sequence[dict]) -> float:
    return sum(float(o.get("realized_pnl", 0.0)) for o in orders if o.get("side") == "sell")


def _naive(dt: datetime) -> datetime:
    """Normalizza a UTC naive (Mongo restituisce datetime senza tzinfo)."""
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def _price_at_or_before(history: Sequence[dict], cutoff: datetime) -> float | None:
    """Ultimo prezzo con ts <= cutoff (history ordinata crescente per ts)."""
    cut = _naive(cutoff)
    chosen = None
    for p in history:
        if _naive(p["ts"]) <= cut:
            chosen = p["prezzo"]
        else:
            break
    return chosen


def _reference_price(history: Sequence[dict], cutoff: datetime) -> float | None:
    """Prezzo di riferimento per una variazione: ultimo <= cutoff, altrimenti il
    primo punto disponibile nella finestra (baseline più antica nota)."""
    ref = _price_at_or_before(history, cutoff)
    if ref is not None:
        return ref
    return float(history[0]["prezzo"]) if history else None


# ───────────────────────── DB ─────────────────────────
async def volume_qty(db, *, since: datetime, until: datetime | None = None, athlete_id=None) -> int:
    match: dict = {"created_at": {"$gte": since}}
    if until is not None:
        match["created_at"]["$lte"] = until
    if athlete_id is not None:
        match["athlete_id"] = athlete_id
    orders = await db.orders.find(match, {"qty": 1, "_id": 0}).to_list(length=1_000_000)
    return sum(int(o.get("qty", 0)) for o in orders)


async def count_holders(db, athlete_id) -> int:
    return await db.holdings.count_documents({"athlete_id": athlete_id, "quantity": {"$gt": 0}})


async def _most_traded(db, *, since: datetime, limit: int = 5) -> list[dict]:
    pipeline = [
        {"$match": {"created_at": {"$gte": since}}},
        {"$group": {"_id": "$athlete_id", "qty": {"$sum": "$qty"}}},
        {"$sort": {"qty": -1}},
        {"$limit": limit},
    ]
    rows = await db.orders.aggregate(pipeline).to_list(length=limit)
    return [{"athlete_id": str(r["_id"]), "volume": int(r["qty"])} for r in rows]


async def market_overview(db, *, now: datetime | None = None) -> dict:
    now = now or utc_now()
    athletes = await db.athletes.find({"status": "ACTIVE"}).to_list(length=100_000)

    total_cap = sum(
        float(a.get("float_quote", 0)) * float(a.get("prezzo_corrente_eur", 0.0)) for a in athletes
    )
    # var 24h per atleta — UNA aggregazione (no N+1): prezzo di riferimento = primo
    # punto price_history nella finestra delle ultime ~24h.
    ref_rows = await db.price_history.aggregate([
        {"$match": {"ts": {"$gte": now - timedelta(hours=25)}}},
        {"$addFields": {"_p": {"$ifNull": ["$prezzo", "$price"]}}},
        {"$sort": {"ts": 1}},
        {"$group": {"_id": "$athlete_id", "ref": {"$first": "$_p"}}},
    ]).to_list(length=100_000)
    ref_by_aid = {r["_id"]: float(r["ref"]) for r in ref_rows if r.get("ref")}
    var_rows: list[dict] = []
    for a in athletes:
        ref = ref_by_aid.get(a["_id"])
        if not ref:
            continue
        var_rows.append({"athlete_id": str(a["_id"]), "display_label": a.get("display_label"),
                         "var_pct": pct_change(ref, float(a.get("prezzo_corrente_eur", 0.0)))})
    movers = top_movers(var_rows, n=5)

    return {
        "active_count": len(athletes),
        "total_market_cap": total_cap,
        "volume_24h": await volume_qty(db, since=now - timedelta(hours=24)),
        "volume_7d": await volume_qty(db, since=now - timedelta(days=7)),
        "top_gainers": movers["gainers"],
        "top_losers": movers["losers"],
        "most_traded": await _most_traded(db, since=now - timedelta(hours=24)),
        "price_distribution": price_distribution_by(athletes, "role"),
    }


async def athlete_market_stats(db, athlete_id, *, now: datetime | None = None) -> dict:
    now = now or utc_now()
    a = await db.athletes.find_one({"_id": athlete_id})
    if not a:
        return {}
    cur = float(a.get("prezzo_corrente_eur", 0.0))
    equo = float(a.get("prezzo_equo_eur") or a.get("prezzo_corrente_eur", 0.0))
    float_q = float(a.get("float_quote", 0))
    disponibili = int(a.get("primary_pool_qty", float_q - float(a.get("circulating_qty", 0))))
    posseduta = max(0.0, float_q - disponibili)
    hist = await db.price_history.find(
        {"athlete_id": athlete_id}, {"_id": 0, "ts": 1, "prezzo": 1}
    ).sort("ts", 1).to_list(length=100_000)
    prezzi = [float(p["prezzo"]) for p in hist]
    ref24 = _reference_price(hist, now - timedelta(hours=24))
    ref7 = _reference_price(hist, now - timedelta(days=7))
    return {
        "athlete_id": str(athlete_id),
        "prezzo_corrente": cur,
        "market_cap": float_q * cur,
        "valore": float_q * cur,                       # = prezzo × float (numero leggibile in UI)
        "market_value_eur": float_q * cur,             # D7: value = prezzo × FLOAT (unica scala)
        "disponibili": disponibili,                    # quote residue nel pool del banco (finito-duro)
        "posseduta_pct": (posseduta / float_q * 100.0) if float_q else 0.0,
        "sold_out": disponibili <= 0,
        "var_24h_pct": pct_change(ref24, cur) if ref24 else None,
        "var_7d_pct": pct_change(ref7, cur) if ref7 else None,
        "max": max(prezzi) if prezzi else cur,
        "min": min(prezzi) if prezzi else cur,
        "volume_24h": await volume_qty(db, since=now - timedelta(hours=24), athlete_id=athlete_id),
        "volume_7d": await volume_qty(db, since=now - timedelta(days=7), athlete_id=athlete_id),
        "n_holders": await count_holders(db, athlete_id),
        "deviazione": float(a.get("deviazione", 0.0)),
        "scostamento_vs_equo_pct": pct_change(equo, cur),
        "value_decomposition": decompose_value(a),
        "weekly_stats": synthetic_weekly_stats(a),
    }


async def user_market_stats(db, user_id, *, now: datetime | None = None) -> dict:
    now = now or utc_now()
    portfolio = await build_portfolio_response(db, user_id)
    positions = portfolio["positions"]
    totals = portfolio["totals"]

    orders = await db.orders.find({"user_id": user_id}).to_list(length=100_000)
    txs = await db.wallet_transactions.find({"user_id": user_id}).to_list(length=100_000)
    total_fees = sum(abs(float(t.get("amount", 0.0))) for t in txs
                     if t.get("type") in ("fee_buyer", "fee_seller"))
    inflow = sum(float(t.get("amount", 0.0)) for t in txs if float(t.get("amount", 0.0)) > 0)
    outflow = sum(-float(t.get("amount", 0.0)) for t in txs if float(t.get("amount", 0.0)) < 0)

    best = max(positions, key=lambda p: p.get("pnl_abs", 0.0), default=None)
    worst = min(positions, key=lambda p: p.get("pnl_abs", 0.0), default=None)
    return {
        "equity": totals["total_equity"],
        "cash_eur": totals["cash_eur"],
        "positions_value": totals["positions_value"],
        "unrealized_pnl": totals["total_pnl_abs"],
        "realized_pnl": realized_pnl_from_orders(orders),
        "total_fees": total_fees,
        "credit_flow": {"in": inflow, "out": outflow},
        "allocation_by_role": allocation_by(positions, "role"),
        "allocation_by_team": allocation_by(positions, "team_fantasy_name"),
        "best_position": best,
        "worst_position": worst,
    }
