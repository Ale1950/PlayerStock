"""TDD: ritaratura — rendimento muove l'ÀNCORA e compone con la deviazione;
pressione di trading simulata mantiene l'economia sana."""
from __future__ import annotations

import pytest
from bson import ObjectId

from app.cli.simulate_rounds import apply_rendimento_round, simulate_economy
from app.config.pricing_constants import DEVIAZIONE_CAP, FLOOR_PCT_PREZZO_INIZIALE
from app.economy.credit_faucet import PROPOSED_FAUCET
from app.models.common import utc_now


async def _athlete(db, **over):
    aid = ObjectId()
    doc = {
        "_id": aid, "sport_id": "calcio", "status": "ACTIVE", "role": "ATT",
        "prezzo_corrente_eur": 0.0105, "prezzo_iniziale_eur": 0.01,
        "prezzo_equo_eur": 0.01, "deviazione": 0.05, "deviazione_ts": utc_now(),
        "float_quote": 1_000_000, "primary_pool_qty": 1_000_000, "circulating_qty": 0,
        "score_performance": 1.0, "age": 25, "minutaggio_pct": 1.0, "fattore_squadra": 1.0,
    }
    doc.update(over)
    await db.athletes.insert_one(doc)
    return aid


async def test_rendimento_moves_anchor_and_composes_with_deviation(mock_db):
    aid = await _athlete(mock_db)
    now = utc_now()
    await apply_rendimento_round(mock_db, athlete_id=aid, perf_pct=0.10, now=now)
    a = await mock_db.athletes.find_one({"_id": aid})
    assert a["prezzo_equo_eur"] == pytest.approx(0.011)            # àncora +10%
    assert a["prezzo_corrente_eur"] == pytest.approx(0.011 * 1.05)  # compone con dev 0.05


async def test_simulate_economy_keeps_prices_within_bands(mock_db):
    # roster + trader simulati
    for i in range(6):
        await _athlete(mock_db, prezzo_corrente_eur=0.01, deviazione=0.0,
                       prezzo_equo_eur=0.01, role=["ATT", "CC", "DIF", "POR"][i % 4])
    traders = []
    for _ in range(8):
        uid = ObjectId()
        await mock_db.user_wallets.insert_one({"user_id": uid, "balance_eur": 10_000.0, "updated_at": utc_now()})
        traders.append(uid)

    rep = await simulate_economy(mock_db, days=30, trader_ids=traders)

    assert rep["days"] == 30
    assert rep["fee_revenue"] >= 0.0
    assert rep.get("credits_injected", 0.0) == 0.0  # nessun faucet senza config
    # nessun prezzo sotto il floor né oltre il tetto deviazione
    for a in await mock_db.athletes.find({}).to_list(length=100):
        floor = FLOOR_PCT_PREZZO_INIZIALE * a["prezzo_iniziale_eur"]
        tetto = a["prezzo_equo_eur"] * (1 + DEVIAZIONE_CAP)
        assert a["prezzo_corrente_eur"] >= floor - 1e-9
        assert a["prezzo_corrente_eur"] <= tetto + 1e-9
        assert abs(a.get("deviazione", 0.0)) <= DEVIAZIONE_CAP + 1e-9


async def test_simulate_economy_with_faucet_injects_credits(mock_db):
    for i in range(4):
        await _athlete(mock_db, prezzo_corrente_eur=0.01, deviazione=0.0,
                       prezzo_equo_eur=0.01, role=["ATT", "CC", "DIF", "POR"][i % 4])
    traders = []
    for _ in range(5):
        uid = ObjectId()
        await mock_db.user_wallets.insert_one({"user_id": uid, "balance_eur": 10_000.0, "updated_at": utc_now()})
        traders.append(uid)

    rep = await simulate_economy(mock_db, days=20, trader_ids=traders, faucet_config=PROPOSED_FAUCET)
    assert rep["credits_injected"] > 0.0
    # le grant sono idempotenti per evento → una per (trader, giorno)
    assert await mock_db.engagement_credit_grants.count_documents({}) == 5 * 20
    # i ledger NACKL NON sono toccati dal faucet
    assert await mock_db.reward_balances.count_documents({}) == 0
