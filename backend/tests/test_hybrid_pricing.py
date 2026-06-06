"""Fase 3b — prezzo ibrido: impatto trading + rientro (mean reversion) verso l'àncora.

TDD. Funzioni pure (decay/impatto/prezzo) + integrazione su execute_buy/sell.
"""
from __future__ import annotations

import math
from datetime import timedelta

import pytest
from bson import ObjectId

from app.config.pricing_constants import (
    DEVIAZIONE_CAP,
    FLOAT_AZIONI_PER_GIOCATORE,
    K_IMPATTO_TRADING,
    LAMBDA_DEVIAZIONE,
)
from app.core.errors import APIError
from app.market.hybrid_pricing import (
    apply_impact,
    current_market_price,
    decay_deviation,
    market_price,
)
from app.market.trade import (
    execute_buy,
    execute_sell,
    snapshot_all_active_prices,
    snapshot_price,
)
from app.models.common import utc_now

HALF_LIFE_S = math.log(2) / LAMBDA_DEVIAZIONE


# ─────────────────────── funzioni pure ───────────────────────
def test_decay_halves_at_half_life():
    assert decay_deviation(0.10, HALF_LIFE_S) == pytest.approx(0.05, rel=1e-6)


def test_decay_towards_zero_over_long_time():
    assert decay_deviation(0.30, HALF_LIFE_S * 40) == pytest.approx(0.0, abs=1e-6)


def test_decay_zero_dt_unchanged():
    assert decay_deviation(0.123, 0.0) == pytest.approx(0.123)


def test_buy_impact_increases_deviation():
    new = apply_impact(0.0, "buy", 30_000, FLOAT_AZIONI_PER_GIOCATORE)
    assert new == pytest.approx(0.045)  # k=1.5 × 30k/1M = +4,5%


def test_sell_impact_decreases_deviation():
    assert apply_impact(0.05, "sell", 30_000, FLOAT_AZIONI_PER_GIOCATORE) == pytest.approx(0.05 - 0.045)


def test_impact_composes():
    d1 = apply_impact(0.0, "buy", 10_000, FLOAT_AZIONI_PER_GIOCATORE)
    d2 = apply_impact(d1, "buy", 10_000, FLOAT_AZIONI_PER_GIOCATORE)
    assert d2 > d1 > 0.0


def test_impact_clamped_at_cap():
    # un ordine enorme non può sfondare il cap
    assert apply_impact(0.0, "buy", 10_000_000, FLOAT_AZIONI_PER_GIOCATORE) == pytest.approx(DEVIAZIONE_CAP)
    assert apply_impact(0.0, "sell", 10_000_000, FLOAT_AZIONI_PER_GIOCATORE) == pytest.approx(-DEVIAZIONE_CAP)


def test_market_price_composes_anchor_and_deviation():
    assert market_price(0.0100, 0.03, 0.0100) == pytest.approx(0.0103)
    # cambia l'àncora (round di rendimento): i due effetti si compongono
    assert market_price(0.0120, 0.03, 0.0100) == pytest.approx(0.0120 * 1.03)


def test_market_price_respects_floor():
    # àncora crollata + deviazione negativa: non scende sotto il 10% dell'iniziale
    assert market_price(0.003, -0.4, 0.0200) == pytest.approx(0.10 * 0.0200)


def test_market_price_capped_above():
    # deviazione fuori scala viene clampata al cap prima del calcolo
    assert market_price(0.0100, 5.0, 0.0100) == pytest.approx(0.0100 * (1 + DEVIAZIONE_CAP))


# ─────────────────────── integrazione (banco) ───────────────────────
async def _setup(db, *, balance=10_000.0, price=0.02, pool=1_000_000):
    uid, aid = ObjectId(), ObjectId()
    await db.user_wallets.insert_one({"user_id": uid, "balance_eur": balance, "updated_at": utc_now()})
    await db.athletes.insert_one({
        "_id": aid, "sport_id": "calcio", "status": "ACTIVE", "role": "ATT",
        "prezzo_corrente_eur": price, "prezzo_iniziale_eur": price,
        "float_quote": 1_000_000, "primary_pool_qty": pool, "circulating_qty": 1_000_000 - pool,
    })
    return uid, aid


async def test_buy_raises_quoted_price(mock_db):
    uid, aid = await _setup(mock_db)
    before = (await mock_db.athletes.find_one({"_id": aid}))["prezzo_corrente_eur"]
    await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=30_000)
    after = (await mock_db.athletes.find_one({"_id": aid}))["prezzo_corrente_eur"]
    assert after > before
    assert after == pytest.approx(0.02 * 1.045, rel=1e-3)  # +4,5% per ordine al cap 3% (k=1.5)


async def test_repeated_buys_compound_slippage(mock_db):
    uid, aid = await _setup(mock_db)
    t0 = utc_now()
    await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=10_000, now=t0)
    p1 = (await mock_db.athletes.find_one({"_id": aid}))["prezzo_corrente_eur"]
    await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=10_000, now=t0)
    p2 = (await mock_db.athletes.find_one({"_id": aid}))["prezzo_corrente_eur"]
    assert p2 > p1 > 0.02


async def test_sell_lowers_quoted_price(mock_db):
    uid, aid = await _setup(mock_db)
    t0 = utc_now()
    await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=30_000, now=t0)
    # vende dopo l'holding minimo; il rientro avrà quasi azzerato la deviazione,
    # quindi la vendita spinge il prezzo sotto l'àncora
    await execute_sell(mock_db, user_id=uid, athlete_id=aid, qty=30_000, now=t0 + timedelta(days=8))
    after = (await mock_db.athletes.find_one({"_id": aid}))["prezzo_corrente_eur"]
    assert after < 0.02


async def test_price_reverts_towards_anchor_over_time(mock_db):
    uid, aid = await _setup(mock_db)
    t0 = utc_now()
    await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=30_000, now=t0)
    peak = (await mock_db.athletes.find_one({"_id": aid}))["prezzo_corrente_eur"]
    # snapshot dopo l'emivita: il prezzo rientra verso l'àncora (0.02) ma non sotto
    await snapshot_price(mock_db, athlete_id=aid, now=t0 + timedelta(seconds=HALF_LIFE_S))
    reverted = (await mock_db.athletes.find_one({"_id": aid}))["prezzo_corrente_eur"]
    assert 0.02 < reverted < peak
    assert await mock_db.price_history.count_documents({"reason": "snapshot"}) == 1


async def test_price_stays_within_floor_and_cap(mock_db):
    uid, aid = await _setup(mock_db, balance=10_000_000.0)
    t0 = utc_now()
    # molti acquisti consecutivi non sfondano il cap (+DEVIAZIONE_CAP)
    for _ in range(20):
        await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=1_000, now=t0)
    a = await mock_db.athletes.find_one({"_id": aid})
    assert a["prezzo_corrente_eur"] <= 0.02 * (1 + DEVIAZIONE_CAP) + 1e-9
    assert a["deviazione"] <= DEVIAZIONE_CAP + 1e-9


async def test_trade_writes_price_history(mock_db):
    uid, aid = await _setup(mock_db)
    await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=100)
    assert await mock_db.price_history.count_documents({"reason": "trade"}) == 1


async def test_deviation_update_is_atomic_with_order(mock_db):
    # un ordine fallito (fondi insufficienti) NON deve muovere la deviazione
    uid, aid = await _setup(mock_db, balance=1.0)
    with pytest.raises(APIError):
        await execute_buy(mock_db, user_id=uid, athlete_id=aid, qty=30_000)
    a = await mock_db.athletes.find_one({"_id": aid})
    assert a.get("deviazione", 0.0) == pytest.approx(0.0)
    assert a["prezzo_corrente_eur"] == pytest.approx(0.02)


async def test_snapshot_all_active_writes_one_point_each(mock_db):
    await _setup(mock_db)
    await _setup(mock_db)
    n = await snapshot_all_active_prices(mock_db, now=utc_now())
    assert n == 2
    assert await mock_db.price_history.count_documents({"reason": "snapshot"}) == 2


async def test_current_market_price_decays_to_anchor(mock_db):
    # helper pura su documento: dopo molto tempo la deviazione svanisce
    a = {"prezzo_corrente_eur": 0.0206, "prezzo_equo_eur": 0.02,
         "prezzo_iniziale_eur": 0.02, "deviazione": 0.03}
    now = utc_now()
    a["deviazione_ts"] = now - timedelta(seconds=HALF_LIFE_S * 50)
    assert current_market_price(a, now) == pytest.approx(0.02, abs=1e-5)
