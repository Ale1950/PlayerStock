"""News / Eventi di mercato (Engage) — feed da DATI INTERNI (niente web).

Top mover settimana (con SPIEGAZIONE sportiva sintetica) · giocatori ESAURITI ·
news PERSONALIZZATE sulle posizioni dell'utente. **Informativo: nessun premio** →
nessun carico sul faucet.
"""
from __future__ import annotations

import datetime as dt

from bson import ObjectId

from app.models.common import utc_now
from app.modules.stats.service import market_overview
from app.valuation.synthetic_stats import synthetic_weekly_stats


async def _explain(db, athlete_id_str: str) -> str:
    """Perché il prezzo si è mosso: evento sportivo sintetico dell'ultima settimana."""
    try:
        a = await db.athletes.find_one({"_id": ObjectId(athlete_id_str)})
    except Exception:
        a = None
    if not a:
        return "movimento di mercato"
    lw = synthetic_weekly_stats(
        role=a["role"], external_id=str(a.get("source_external_id") or a["_id"]),
        score=float(a.get("score_performance", 1.0)), minutaggio=float(a.get("minutaggio_pct", 0.7)),
    )["last_week"]
    if a["role"] == "POR" and (lw.get("parate") or 0) >= 2:
        return f"{lw['parate']} parate in settimana"
    if (lw.get("gol") or 0) > 0:
        return f"{lw['gol']} gol in settimana"
    if (lw.get("assist") or 0) > 0:
        return f"{lw['assist']} assist in settimana"
    return "flusso di mercato"


async def market_news(db, user_id, *, now: dt.datetime | None = None, limit: int = 12) -> dict:
    now = now or utc_now()
    ov = await market_overview(db, now=now)
    items: list[dict] = []

    for m in ov.get("top_gainers", [])[:2]:
        items.append({"type": "gainer", "tone": "green",
                      "title": f"{m.get('display_label') or '—'} ▲ +{(m.get('var_pct') or 0):.1f}%",
                      "detail": await _explain(db, m["athlete_id"])})
    for m in ov.get("top_losers", [])[:2]:
        items.append({"type": "loser", "tone": "red",
                      "title": f"{m.get('display_label') or '—'} ▼ {(m.get('var_pct') or 0):.1f}%",
                      "detail": await _explain(db, m["athlete_id"])})

    sold = await db.athletes.find(
        {"status": "ACTIVE", "primary_pool_qty": {"$lte": 0}}, {"display_label": 1}
    ).limit(3).to_list(length=3)
    for a in sold:
        items.append({"type": "soldout", "tone": "amber",
                      "title": f"{a.get('display_label') or '—'} · ESAURITO",
                      "detail": "nessuna quota nel pool finché qualcuno non vende"})

    # personalizzate: le TUE posizioni che si muovono molto (≥2%)
    holdings = await db.holdings.find({"user_id": user_id, "quantity": {"$gt": 0}}).to_list(length=200)
    for h in holdings:
        a = await db.athletes.find_one({"_id": h["athlete_id"]}, {"display_label": 1, "prezzo_corrente_eur": 1})
        ref_doc = await db.price_history.find(
            {"athlete_id": h["athlete_id"]}, {"_id": 0, "prezzo": 1, "price": 1}
        ).sort("ts", 1).limit(1).to_list(length=1)
        if not a or not ref_doc:
            continue
        ref = float(ref_doc[0].get("prezzo", ref_doc[0].get("price", 0.0)))
        cur = float(a.get("prezzo_corrente_eur", 0.0))
        if ref:
            var = (cur / ref - 1) * 100
            if abs(var) >= 2:
                items.append({"type": "you", "tone": "cyan" if var >= 0 else "red",
                              "title": f"La tua posizione: {a.get('display_label') or '—'} "
                                       f"{'▲ +' if var >= 0 else '▼ '}{var:.1f}%",
                              "detail": "forte movimento su un titolo che possiedi"})

    return {"items": items[:limit]}
