"""TDD: feed News/Eventi di mercato — da DATI INTERNI, informativo (nessun premio)."""
from __future__ import annotations

import datetime as dt

from bson import ObjectId

from app.models.common import utc_now
from app.modules.engagement.news import market_news


async def _athlete(db, *, price, role="ATT", pool=1_000_000, label="X", score=1.4):
    aid = ObjectId()
    await db.athletes.insert_one({
        "_id": aid, "sport_id": "calcio", "status": "ACTIVE", "role": role,
        "prezzo_corrente_eur": price, "prezzo_iniziale_eur": 0.01, "prezzo_equo_eur": 0.01,
        "float_quote": 1_000_000, "primary_pool_qty": pool, "display_label": label,
        "source_external_id": label, "score_performance": score, "age": 24, "minutaggio_pct": 1.0,
        "fattore_squadra": 1.0,
    })
    return aid


async def test_market_news_mixed_feed(mock_db):
    now = utc_now()
    uid = ObjectId()
    gain = await _athlete(mock_db, price=0.03, label="Souza")   # salirà
    await mock_db.price_history.insert_one({"athlete_id": gain, "prezzo": 0.02, "ts": now - dt.timedelta(hours=20)})
    await _athlete(mock_db, price=0.005, label="Esausto", pool=0)  # esaurito
    await mock_db.holdings.insert_one({"user_id": uid, "athlete_id": gain, "quantity": 100,
                                       "lots": [{"qty": 100, "price": 0.02, "acquired_at": now}]})

    res = await market_news(mock_db, uid, now=now)
    items = res["items"]
    types = {i["type"] for i in items}
    assert "gainer" in types
    assert "soldout" in types
    assert "you" in types                      # news personalizzata sulla mia posizione
    assert all("reward" not in i for i in items)   # INFORMATIVO: nessun premio
    # ogni item ha titolo + dettaglio + tono
    assert all({"type", "title", "detail", "tone"} <= set(i) for i in items)
