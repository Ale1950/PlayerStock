"""TDD: backbone dati / aggregati (market-wide, per-giocatore, per-utente)."""
from __future__ import annotations

from datetime import timedelta

import pytest
from bson import ObjectId

from app.models.common import utc_now
from app.modules.stats.service import (
    allocation_by,
    athlete_market_stats,
    count_holders,
    decompose_value,
    market_overview,
    pct_change,
    price_distribution_by,
    realized_pnl_from_orders,
    summarize,
    top_movers,
    user_market_stats,
    volume_qty,
)


# ───────────────────────── pure ─────────────────────────
def test_pct_change():
    assert pct_change(0.01, 0.011) == pytest.approx(10.0)
    assert pct_change(0.0, 0.5) is None


def test_summarize():
    s = summarize([0.01, 0.02, 0.03])
    assert s == {"count": 3, "min": pytest.approx(0.01), "max": pytest.approx(0.03), "avg": pytest.approx(0.02)}
    assert summarize([])["count"] == 0


def test_price_distribution_by_role():
    athletes = [
        {"role": "ATT", "prezzo_corrente_eur": 0.03},
        {"role": "ATT", "prezzo_corrente_eur": 0.05},
        {"role": "POR", "prezzo_corrente_eur": 0.01},
    ]
    dist = price_distribution_by(athletes, "role")
    assert dist["ATT"]["count"] == 2
    assert dist["ATT"]["avg"] == pytest.approx(0.04)
    assert dist["POR"]["count"] == 1


def test_top_movers():
    rows = [
        {"athlete_id": "a", "var_pct": 5.0},
        {"athlete_id": "b", "var_pct": -8.0},
        {"athlete_id": "c", "var_pct": 2.0},
    ]
    mv = top_movers(rows, n=2)
    assert [r["athlete_id"] for r in mv["gainers"]] == ["a", "c"]
    assert mv["losers"][0]["athlete_id"] == "b"


def test_decompose_value():
    # D7: valore_equo = ancora € × FLOAT; i fattori restano audit sintetico del rank.
    a = {"role": "ATT", "score_performance": 1.0, "age": 25,
         "minutaggio_pct": 1.0, "fattore_squadra": 1.0,
         "prezzo_equo_eur": 12.0, "float_quote": 1_000_000}
    d = decompose_value(a)
    assert d["base_ruolo"] == pytest.approx(1.18)
    assert d["f_score"] == pytest.approx(1.0)
    assert d["valore_equo"] == pytest.approx(12.0 * 1_000_000)


def test_allocation_by():
    positions = [
        {"role": "ATT", "current_value": 60.0},
        {"role": "ATT", "current_value": 30.0},
        {"role": "CC", "current_value": 10.0},
    ]
    alloc = {a["key"]: a for a in allocation_by(positions, "role")}
    assert alloc["ATT"]["value"] == pytest.approx(90.0)
    assert alloc["ATT"]["pct"] == pytest.approx(90.0)
    assert alloc["CC"]["pct"] == pytest.approx(10.0)


def test_realized_pnl_from_orders():
    orders = [
        {"side": "sell", "realized_pnl": 3.0},
        {"side": "sell", "realized_pnl": -1.0},
        {"side": "buy"},
    ]
    assert realized_pnl_from_orders(orders) == pytest.approx(2.0)


# ───────────────────────── DB ─────────────────────────
async def _athlete(db, *, price=0.02, role="ATT", float_q=1_000_000, circ=0):
    aid = ObjectId()
    await db.athletes.insert_one({
        "_id": aid, "sport_id": "calcio", "status": "ACTIVE", "role": role,
        "prezzo_corrente_eur": price, "prezzo_iniziale_eur": price,
        "prezzo_equo_eur": price, "float_quote": float_q, "circulating_qty": circ,
        "score_performance": 1.0, "age": 25, "minutaggio_pct": 1.0, "fattore_squadra": 1.0,
    })
    return aid


async def test_volume_qty_window(mock_db):
    aid = await _athlete(mock_db)
    now = utc_now()
    await mock_db.orders.insert_one({"athlete_id": aid, "side": "buy", "qty": 100, "created_at": now})
    await mock_db.orders.insert_one({"athlete_id": aid, "side": "sell", "qty": 40, "created_at": now})
    await mock_db.orders.insert_one({"athlete_id": aid, "side": "buy", "qty": 999, "created_at": now - timedelta(days=3)})
    vol = await volume_qty(mock_db, since=now - timedelta(days=1))
    assert vol == 140


async def test_count_holders(mock_db):
    aid = await _athlete(mock_db)
    await mock_db.holdings.insert_one({"user_id": ObjectId(), "athlete_id": aid, "quantity": 10})
    await mock_db.holdings.insert_one({"user_id": ObjectId(), "athlete_id": aid, "quantity": 0})
    assert await count_holders(mock_db, aid) == 1


async def test_market_overview(mock_db):
    now = utc_now()
    a1 = await _athlete(mock_db, price=0.03, role="ATT")
    a2 = await _athlete(mock_db, price=0.01, role="POR")
    await mock_db.orders.insert_one({"athlete_id": a1, "side": "buy", "qty": 500, "created_at": now})
    # a1 sale: ref 0.02 (20h fa) → current 0.03 = +50% → deve comparire tra i gainers
    await mock_db.price_history.insert_one({"athlete_id": a1, "prezzo": 0.02, "ts": now - timedelta(hours=20)})
    ov = await market_overview(mock_db, now=now)
    assert ov["active_count"] == 2
    # market cap = Σ float × prezzo = 1M×0.03 + 1M×0.01 = 40_000
    assert ov["total_market_cap"] == pytest.approx(40_000.0)
    assert ov["volume_24h"] == 500
    assert "ATT" in ov["price_distribution"]
    assert ov["top_gainers"] and ov["top_gainers"][0]["athlete_id"] == str(a1)
    assert ov["top_gainers"][0]["var_pct"] == pytest.approx(50.0)


async def test_athlete_market_stats(mock_db):
    now = utc_now()
    aid = await _athlete(mock_db, price=0.025)
    await mock_db.price_history.insert_one({"athlete_id": aid, "prezzo": 0.02, "ts": now - timedelta(hours=20)})
    await mock_db.price_history.insert_one({"athlete_id": aid, "prezzo": 0.025, "ts": now})
    await mock_db.holdings.insert_one({"user_id": ObjectId(), "athlete_id": aid, "quantity": 5})
    st = await athlete_market_stats(mock_db, aid, now=now)
    assert st["market_cap"] == pytest.approx(1_000_000 * 0.025)
    assert st["n_holders"] == 1
    assert st["var_24h_pct"] == pytest.approx(25.0)  # 0.02 → 0.025
    assert st["max"] == pytest.approx(0.025)
    assert "valore_equo" in st["value_decomposition"]
    assert "season" in st["weekly_stats"] and "last_week" in st["weekly_stats"]
    assert st["disponibili"] == 1_000_000          # pool residuo (finito-duro)
    assert st["posseduta_pct"] == pytest.approx(0.0)
    assert st["sold_out"] is False
    assert st["valore"] == pytest.approx(1_000_000 * 0.025)


async def test_user_market_stats_realized_and_allocation(mock_db):
    from app.market.trade import execute_buy, execute_sell
    uid = ObjectId()
    await mock_db.user_wallets.insert_one({"user_id": uid, "balance_eur": 10_000.0, "updated_at": utc_now()})
    aid = await _athlete(mock_db, price=0.02)
    await mock_db.athletes.update_one({"_id": aid}, {"$set": {"primary_pool_qty": 1_000_000}})
    t0 = utc_now()
    await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=1_000, now=t0)
    await execute_sell(mock_db, user_id=uid, athlete_id=aid, qty=400, now=t0 + timedelta(days=8))
    st = await user_market_stats(mock_db, uid, now=t0 + timedelta(days=8))
    assert st["realized_pnl"] == pytest.approx(
        (await mock_db.orders.find_one({"side": "sell"}))["realized_pnl"]
    )
    assert st["total_fees"] > 0
    assert any(a["key"] == "ATT" for a in st["allocation_by_role"])
