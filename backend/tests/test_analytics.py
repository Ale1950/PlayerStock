"""TDD: analytics portafoglio — equity ricostruita + indici + confronti (Atlas-like)."""
from __future__ import annotations

from datetime import timedelta

import pytest
from bson import ObjectId

from app.models.common import utc_now
from app.modules.stats.analytics import (
    leaderboard_analytics,
    reconstruct_equity,
    user_analytics,
)


async def _seed(db, *, cash=50.0, qty=100):
    uid, aid = ObjectId(), ObjectId()
    now = utc_now()
    await db.user_wallets.insert_one({"user_id": uid, "balance_eur": cash, "updated_at": now})
    await db.athletes.insert_one({
        "_id": aid, "sport_id": "calcio", "status": "ACTIVE", "role": "ATT",
        "prezzo_corrente_eur": 0.03, "prezzo_iniziale_eur": 0.01,
        "prezzo_equo_eur": 0.01, "float_quote": 1_000_000,
        "display_label": "Best One", "team_fantasy_id": ObjectId(),
        "score_performance": 1.0, "age": 25, "minutaggio_pct": 1.0, "fattore_squadra": 1.0,
    })
    await db.holdings.insert_one({"user_id": uid, "athlete_id": aid, "quantity": qty,
                                  "lots": [{"qty": qty, "price": 0.02, "acquired_at": now - timedelta(days=20)}]})
    for d, p in [(10, 0.02), (5, 0.025), (1, 0.03)]:
        await db.price_history.insert_one({"athlete_id": aid, "prezzo": p, "ts": now - timedelta(days=d)})
    return uid, aid


async def test_reconstruct_equity_uses_cash_plus_holdings(mock_db):
    uid, aid = await _seed(mock_db, cash=50.0, qty=100)
    gran = "day"
    pts = await reconstruct_equity(mock_db, uid, utc_now() - timedelta(days=31), gran)
    assert len(pts) >= 2
    assert pts[-1]["equity"] == pytest.approx(50.0 + 100 * 0.03)  # cassa + qty×ultimo prezzo


async def test_user_analytics_shape_and_indices(mock_db):
    uid, aid = await _seed(mock_db)
    res = await user_analytics(mock_db, uid, period="1M")
    assert res["granularity"] in ("day", "week")
    assert len(res["equity"]["points"]) >= 2
    assert set(res["portfolio_indices"]) == {"return_pct", "volatility", "max_drawdown", "beta", "sharpe"}
    assert len(res["positions"]) == 1
    pos = res["positions"][0]
    assert pos["display_label"] == "Best One"
    assert "indices" in pos and "series" in pos
    assert "market_best_player" in res  # overlay confronto
    # un solo utente → best_user può essere None, ma la chiave c'è
    assert "best_user" in res


async def test_leaderboard_analytics_metrics_and_privacy(mock_db):
    uid1, aid = await _seed(mock_db, cash=50.0, qty=100)        # equity ~53
    uid2 = ObjectId()
    await mock_db.user_wallets.insert_one({"user_id": uid2, "balance_eur": 20.0, "updated_at": utc_now()})
    await mock_db.holdings.insert_one({"user_id": uid2, "athlete_id": aid, "quantity": 50,
                                       "lots": [{"qty": 50, "price": 0.02, "acquired_at": utc_now()}]})
    await mock_db.users.insert_one({"_id": uid1, "name": "Mario Rossi", "status": "active"})
    await mock_db.users.insert_one({"_id": uid2, "name": "Luigi Verdi", "status": "active"})
    await mock_db.orders.insert_one({"user_id": uid1, "side": "sell", "realized_pnl": 2.0})

    res = await leaderboard_analytics(mock_db, uid1, period="1M", limit=10)
    items = res["items"]
    assert len(items) == 2
    assert items[0]["equity"] >= items[1]["equity"]          # ordinati per patrimonio
    me = next(i for i in items if i["is_self"])
    assert set(me) >= {"rank", "pseudonym", "is_self", "equity", "return_pct",
                       "roi_vs_market_pct", "win_rate", "volatility", "return_week_pct", "trend"}
    assert me["win_rate"] == pytest.approx(100.0)             # 1 vendita in profitto
    # PRIVACY: mai nomi reali, solo pseudonimi
    assert "Mario Rossi" not in [i["pseudonym"] for i in items]
    assert "Luigi Verdi" not in [i["pseudonym"] for i in items]


async def test_empty_portfolio_is_clean(mock_db):
    uid = ObjectId()
    await mock_db.user_wallets.insert_one({"user_id": uid, "balance_eur": 10_000.0, "updated_at": utc_now()})
    res = await user_analytics(mock_db, uid, period="1S")
    assert res["positions"] == []
    assert res["equity"]["points"] == []
