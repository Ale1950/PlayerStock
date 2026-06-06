"""Analytics portafoglio (Fase Design Gruppo 2) — calcolo INTERNO.

- EQUITY nel tempo RICOSTRUITA da price_history × holdings correnti + cassa
  (approssimazione MVP: holdings/cassa costanti sulla finestra; va bene per la curva
  "quanto valgono oggi i miei titoli storicamente"). Bucket ADATTIVO (giorni/settimane).
- Indici per posizione e per portafoglio (rendimento/volatilità/maxDD/beta/Sharpe).
- Confronti: miglior giocatore di mercato (overlay) · miglior utente (solo PSEUDONIMO).
"""
from __future__ import annotations

import datetime as dt
from typing import Sequence

from app.economy.indices import (
    bucket_points,
    choose_granularity,
    portfolio_indices,
    total_return_pct,
    volatility,
    win_rate,
)
from app.economy.indices import _key as _bkey  # noqa: PLC2701
from app.models.common import utc_now
from app.modules.portfolio.service import anonymize_display_name


def _naive(d: dt.datetime) -> dt.datetime:
    return d.astimezone(dt.timezone.utc).replace(tzinfo=None) if d.tzinfo else d


async def _series(db, athlete_id, since: dt.datetime) -> list[dict]:
    cur = db.price_history.find(
        {"athlete_id": athlete_id, "ts": {"$gte": since}},
        {"_id": 0, "ts": 1, "prezzo": 1, "price": 1},
    ).sort("ts", 1)
    raw = await cur.to_list(length=10_000)
    return [{"ts": p["ts"], "value": float(p.get("prezzo", p.get("price", 0.0)))} for p in raw]


async def _bucketed(db, athlete_id, since, gran) -> list[dict]:
    s = await _series(db, athlete_id, since)
    if not s:
        a = await db.athletes.find_one({"_id": athlete_id}, {"prezzo_corrente_eur": 1})
        if a:
            s = [{"ts": utc_now(), "value": float(a.get("prezzo_corrente_eur", 0.0))}]
    return bucket_points(s, gran)


async def reconstruct_equity(db, user_id, since: dt.datetime, gran: str) -> list[dict]:
    """Equity bucketata = cassa + Σ qty × prezzo (forward-fill per bucket)."""
    w = await db.user_wallets.find_one({"user_id": user_id})
    cash = float(w["balance_eur"]) if w else 0.0
    holdings = await db.holdings.find({"user_id": user_id, "quantity": {"$gt": 0}}).to_list(length=1000)
    if not holdings:
        return []

    per: list[dict] = []
    for h in holdings:
        bp = await _bucketed(db, h["athlete_id"], since, gran)
        per.append({
            "qty": h["quantity"],
            "price_by_key": {_bkey(p["ts"], gran): p["value"] for p in bp},
            "ts_by_key": {_bkey(p["ts"], gran): p["ts"] for p in bp},
            "first": bp[0]["value"] if bp else 0.0,
        })
    keys: set[str] = set()
    ts_by_key: dict[str, dt.datetime] = {}
    for a in per:
        keys |= set(a["price_by_key"].keys())
        ts_by_key.update(a["ts_by_key"])
    if not keys:
        return []
    last = [a["first"] for a in per]
    out: list[dict] = []
    for k in sorted(keys):
        eq = cash
        for i, a in enumerate(per):
            if k in a["price_by_key"]:
                last[i] = a["price_by_key"][k]
            eq += a["qty"] * last[i]
        out.append({"ts": ts_by_key[k], "equity": eq})
    return out


async def _market_index(db, since, gran, sample: int = 40) -> list[float]:
    """Indice di mercato = media dei prezzi bucketati su un campione di atleti attivi."""
    ath = await db.athletes.find({"status": "ACTIVE"}, {"_id": 1}).limit(sample).to_list(length=sample)
    by_key: dict[str, list[float]] = {}
    for a in ath:
        for p in await _bucketed(db, a["_id"], since, gran):
            by_key.setdefault(_bkey(p["ts"], gran), []).append(p["value"])
    return [sum(v) / len(v) for k, v in sorted(by_key.items())]


def _price_at_or_before(series: Sequence[dict], cutoff: dt.datetime) -> float | None:
    cut = _naive(cutoff)
    chosen = None
    for p in series:
        if _naive(p["ts"]) <= cut:
            chosen = p["value"]
        else:
            break
    return chosen


async def _position(db, holding, since, gran, market: list[float]) -> dict:
    aid = holding["athlete_id"]
    a = await db.athletes.find_one({"_id": aid}) or {}
    bp = await _bucketed(db, aid, since, gran)
    prices = [p["value"] for p in bp]
    cur = float(a.get("prezzo_corrente_eur", prices[-1] if prices else 0.0))
    # delta vs settimana / mese precedente (su storico completo)
    full = await _series(db, aid, utc_now() - dt.timedelta(days=45))
    now = utc_now()
    p7 = _price_at_or_before(full, now - dt.timedelta(days=7))
    p30 = _price_at_or_before(full, now - dt.timedelta(days=30))
    return {
        "athlete_id": str(aid),
        "display_label": a.get("display_label"),
        "role": a.get("role"),
        "quantity": holding["quantity"],
        "team_color_primary": None,  # arricchito lato UI dal portfolio
        "series": [{"ts": p["ts"], "price": p["value"]} for p in bp],
        "delta_week_pct": ((cur / p7 - 1) * 100.0) if p7 else None,
        "delta_month_pct": ((cur / p30 - 1) * 100.0) if p30 else None,
        "indices": portfolio_indices(prices, market=market) if len(prices) >= 2 else
        {"return_pct": 0.0, "volatility": 0.0, "max_drawdown": 0.0, "beta": 0.0, "sharpe": 0.0},
    }


async def _best_user(db, user_id, since, gran) -> dict | None:
    """Miglior utente per equity corrente (escluso se stesso). Solo PSEUDONIMO."""
    pipe = [{"$match": {"quantity": {"$gt": 0}}},
            {"$group": {"_id": "$user_id", "n": {"$sum": 1}}}]
    rows = await db.holdings.aggregate(pipe).to_list(length=10000)
    prices = {a["_id"]: float(a.get("prezzo_corrente_eur", 0.0))
              for a in await db.athletes.find({}, {"prezzo_corrente_eur": 1}).to_list(length=10000)}
    best, best_eq = None, -1.0
    for r in rows:
        uid = r["_id"]
        if uid == user_id:
            continue
        hs = await db.holdings.find({"user_id": uid, "quantity": {"$gt": 0}}).to_list(length=1000)
        eq = sum(h["quantity"] * prices.get(h["athlete_id"], 0.0) for h in hs)
        if eq > best_eq:
            best, best_eq = uid, eq
    if best is None:
        return None
    u = await db.users.find_one({"_id": best}, {"name": 1})
    pts = await reconstruct_equity(db, best, since, gran)
    vals = [p["equity"] for p in pts]
    return {
        "pseudonym": anonymize_display_name((u or {}).get("name"), is_self=False),
        "equity": {"points": pts},
        "return_pct": total_return_pct(vals) or 0.0,
    }


def _equity_return_since(ser: list[dict], cutoff: dt.datetime) -> float | None:
    if not ser:
        return None
    pts = [{"ts": p["ts"], "value": p["equity"]} for p in ser]
    v = _price_at_or_before(pts, cutoff)
    last = ser[-1]["equity"]
    return (last / v - 1) * 100.0 if v else None


async def leaderboard_analytics(db, current_user_id, *, period: str = "1M", limit: int = 20) -> dict:
    """Classifica utenti con stat FINANZIARIE. SOLO PSEUDONIMI, mai nome reale."""
    gran, days = choose_granularity(period)
    since = utc_now() - dt.timedelta(days=days)
    market = await _market_index(db, since, gran)
    mret = total_return_pct(market) or 0.0

    prices = {a["_id"]: float(a.get("prezzo_corrente_eur", 0.0))
              for a in await db.athletes.find({}, {"prezzo_corrente_eur": 1}).to_list(length=10000)}
    grp = await db.holdings.aggregate([
        {"$match": {"quantity": {"$gt": 0}}},
        {"$group": {"_id": "$user_id", "hs": {"$push": {"a": "$athlete_id", "q": "$quantity"}}}},
    ]).to_list(length=10000)
    eq_by_user = {r["_id"]: sum(h["q"] * prices.get(h["a"], 0.0) for h in r["hs"]) for r in grp}
    ranked = sorted(eq_by_user.items(), key=lambda kv: kv[1], reverse=True)

    sel = {uid for uid, _ in ranked[:limit]}
    if current_user_id in eq_by_user:
        sel.add(current_user_id)

    items: list[dict] = []
    for rank, (uid, eq) in enumerate(ranked, start=1):
        if uid not in sel:
            continue
        ser = await reconstruct_equity(db, uid, since, gran)
        vals = [p["equity"] for p in ser]
        ret = total_return_pct(vals) or 0.0
        orders = await db.orders.find({"user_id": uid}).to_list(length=10000)
        u = await db.users.find_one({"_id": uid}, {"name": 1})
        items.append({
            "rank": rank,
            "pseudonym": anonymize_display_name((u or {}).get("name"), is_self=False),
            "is_self": uid == current_user_id,
            "equity": eq,
            "return_pct": ret,
            "roi_vs_market_pct": ret - mret,
            "win_rate": win_rate(orders),
            "volatility": volatility(vals),
            "return_week_pct": _equity_return_since(ser, utc_now() - dt.timedelta(days=7)),
            "trend": vals,
        })
    items.sort(key=lambda x: x["rank"])
    return {"items": items, "total_users": len(eq_by_user), "market_return_pct": mret, "period": period}


async def user_analytics(db, user_id, *, period: str = "1M") -> dict:
    gran, days = choose_granularity(period)
    since = utc_now() - dt.timedelta(days=days)
    market = await _market_index(db, since, gran)

    eq = await reconstruct_equity(db, user_id, since, gran)
    eq_vals = [p["equity"] for p in eq]
    pidx = (portfolio_indices(eq_vals, market=market) if len(eq_vals) >= 2
            else {"return_pct": 0.0, "volatility": 0.0, "max_drawdown": 0.0, "beta": 0.0, "sharpe": 0.0})

    holdings = await db.holdings.find({"user_id": user_id, "quantity": {"$gt": 0}}).to_list(length=1000)
    positions = [await _position(db, h, since, gran, market) for h in holdings]

    best_p = await db.athletes.find_one({"status": "ACTIVE"}, sort=[("prezzo_corrente_eur", -1)])
    market_best_player = None
    if best_p:
        bp = await _bucketed(db, best_p["_id"], since, gran)
        market_best_player = {
            "athlete_id": str(best_p["_id"]), "display_label": best_p.get("display_label"),
            "series": [{"ts": p["ts"], "price": p["value"]} for p in bp],
        }

    return {
        "period": period,
        "granularity": gran,
        "equity": {"points": [{"ts": p["ts"], "equity": p["equity"]} for p in eq]},
        "portfolio_indices": pidx,
        "market_best_player": market_best_player,
        "best_user": await _best_user(db, user_id, since, gran),
        "positions": positions,
    }
