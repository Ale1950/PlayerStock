"""Migrazione € (D7) — invarianti strutturali.

- fondo iniziale €1.000.000 e faucet ri-scalato ×100;
- value = price × FLOAT (una sola scala);
- reset_to_euro: wallet €1M, holding/ledger azzerati, atleti con ancora € nel range,
  NACKL (reward_balances) INTATTO.
"""
from __future__ import annotations

import pytest

from app.config.pricing_constants import BUDGET_INIZIALE_UTENTE_EUR, FLOAT_AZIONI_PER_GIOCATORE
from app.economy.credit_faucet import FAUCET
from app.valuation.market_value import market_value_eur_from_price, price_from_market_value


def test_fund_and_faucet_constants():
    assert BUDGET_INIZIALE_UTENTE_EUR == 1_000_000.0
    assert FAUCET["base"] == 25.0
    assert FAUCET["daily_cap"] == 500.0
    # cap = 0,05% del fondo (stesso peso relativo del design Crediti)
    assert FAUCET["daily_cap"] / BUDGET_INIZIALE_UTENTE_EUR == pytest.approx(0.0005)


def test_value_is_price_times_float():
    for price in (0.5, 5.75, 86.30, 115.0):
        assert market_value_eur_from_price(price) == pytest.approx(price * FLOAT_AZIONI_PER_GIOCATORE)
        assert price_from_market_value(price * FLOAT_AZIONI_PER_GIOCATORE) == pytest.approx(price)


@pytest.mark.asyncio
async def test_reset_to_euro_resets_economy_and_keeps_nackl(mock_db):
    from app.cli.reset_to_euro import reset_to_euro
    from bson import ObjectId

    uid = ObjectId()
    await mock_db.users.insert_one({"_id": uid, "email": "x@y.z"})
    # stato "sporco" pre-reset
    await mock_db.user_wallets.insert_one({"user_id": uid, "balance_eur": 123.0})
    await mock_db.holdings.insert_one({"user_id": uid, "athlete_id": ObjectId(), "quantity": 999})
    await mock_db.trades.insert_one({"qty": 1, "price": 1.0})
    # NACKL su ledger separato — NON deve essere toccato
    await mock_db.reward_balances.insert_one({"user_id": uid, "amount": 42.0})
    # atleti per 2 squadre (servono score/fattore per Opzione B)
    docs = []
    for t in ("tA", "tB"):
        for i in range(20):
            docs.append({
                "sport_id": "calcio", "status": "ACTIVE", "team_fantasy_id": t,
                "role": "ATT", "source_external_id": f"{t}{i}", "internal_full_name": f"{t}{i}",
                "score_performance": 2.0 - i * 0.07, "fattore_squadra": 1.25 if t == "tA" else 0.93,
                "float_quote": FLOAT_AZIONI_PER_GIOCATORE,
                "primary_pool_qty": 10, "circulating_qty": 5,  # "sporco"
            })
    await mock_db.athletes.insert_many(docs)

    await reset_to_euro(mock_db)

    # wallet → €1.000.000
    w = await mock_db.user_wallets.find_one({"user_id": uid})
    assert w["balance_eur"] == 1_000_000.0
    # holding / trades azzerati
    assert await mock_db.holdings.count_documents({}) == 0
    assert await mock_db.trades.count_documents({}) == 0
    # welcome bonus presente
    assert await mock_db.wallet_transactions.count_documents({"type": "welcome_bonus"}) == 1
    # NACKL INTATTO
    nackl = await mock_db.reward_balances.find_one({"user_id": uid})
    assert nackl is not None and nackl["amount"] == 42.0
    # atleti: pool IPO ripristinato + ancora € nel range, value = price × FLOAT
    for a in await mock_db.athletes.find({}).to_list(length=100):
        assert a["primary_pool_qty"] == FLOAT_AZIONI_PER_GIOCATORE
        assert a["circulating_qty"] == 0
        assert a["deviazione"] == 0.0
        price = a["prezzo_corrente_eur"]
        assert 0.4 <= price <= 120.0
        assert a["market_value_eur_seed"] == pytest.approx(price * FLOAT_AZIONI_PER_GIOCATORE)
