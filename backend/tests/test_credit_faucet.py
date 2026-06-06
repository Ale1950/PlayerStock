"""TDD: faucet CREDITI da engagement — conversione a scaglioni (marginale) +
accredito idempotente su ledger INDIPENDENTE dal NACKL.

Forma curva (decisa dall'utente): tier1 x3 · tier2 x1.5 · tier3 x0.75 · tier4 x0.2.
Scala/soglie/cap = PROPOSTI (vedi modulo), validati in simulazione.
"""
from __future__ import annotations

import datetime as dt

import pytest
from bson import ObjectId

from app.economy.credit_faucet import (
    PROPOSED_FAUCET,
    grant_engagement_credits,
    tiered_credits,
)

TIERS = [(50, 3.0), (200, 1.5), (500, 0.75), (None, 0.2)]


# ───────────────────────── pure ─────────────────────────
def test_single_tier():
    assert tiered_credits(0, 50, base=1.0, tiers=TIERS) == pytest.approx(150.0)  # 50×3


def test_crosses_boundary():
    # 0→60: 50×3 + 10×1.5 = 165
    assert tiered_credits(0, 60, base=1.0, tiers=TIERS) == pytest.approx(165.0)


def test_starts_mid_and_crosses():
    # 40→60: 10×3 + 10×1.5 = 45
    assert tiered_credits(40, 20, base=1.0, tiers=TIERS) == pytest.approx(45.0)


def test_diminishing_returns_bite():
    early = tiered_credits(0, 10, base=1.0, tiers=TIERS)        # 30 (x3)
    late = tiered_credits(490, 10, base=1.0, tiers=TIERS)        # 7.5 (x0.75)
    grind = tiered_credits(600, 10, base=1.0, tiers=TIERS)       # 2.0 (x0.2)
    assert early == pytest.approx(30.0)
    assert late == pytest.approx(7.5)
    assert grind == pytest.approx(2.0)
    assert early > late > grind


def test_base_scales_linearly():
    assert tiered_credits(0, 10, base=0.25, tiers=TIERS) == pytest.approx(7.5)  # 30×0.25


# ───────────────────────── accrual (DB) ─────────────────────────
async def _wallet(db, uid, bal=10_000.0):
    await db.user_wallets.insert_one({"user_id": uid, "balance_eur": bal, "updated_at": dt.datetime(2026, 1, 1)})


async def test_grant_credits_wallet_and_state(mock_db):
    uid = ObjectId()
    await _wallet(mock_db, uid)
    now = dt.datetime(2026, 1, 1, 12, 0)
    cfg = {"base": 1.0, "tiers": TIERS, "daily_cap": 1_000.0}
    res = await grant_engagement_credits(mock_db, user_id=uid, event_id="e1", ep=50, now=now, config=cfg)
    assert res["credits"] == pytest.approx(150.0)
    w = await mock_db.user_wallets.find_one({"user_id": uid})
    assert w["balance_eur"] == pytest.approx(10_150.0)
    st = await mock_db.engagement_credit_state.find_one({"_id": uid})
    assert st["cumulative_ep"] == 50


async def test_grant_is_idempotent(mock_db):
    uid = ObjectId()
    await _wallet(mock_db, uid)
    now = dt.datetime(2026, 1, 1, 12, 0)
    cfg = {"base": 1.0, "tiers": TIERS, "daily_cap": 1_000.0}
    await grant_engagement_credits(mock_db, user_id=uid, event_id="dup", ep=10, now=now, config=cfg)
    r2 = await grant_engagement_credits(mock_db, user_id=uid, event_id="dup", ep=10, now=now, config=cfg)
    assert r2["idempotent"] is True
    w = await mock_db.user_wallets.find_one({"user_id": uid})
    assert w["balance_eur"] == pytest.approx(10_030.0)  # accreditato UNA volta (10×3)
    assert await mock_db.engagement_credit_grants.count_documents({}) == 1


async def test_daily_cap_clamps_payout(mock_db):
    uid = ObjectId()
    await _wallet(mock_db, uid)
    now = dt.datetime(2026, 1, 1, 12, 0)
    cfg = {"base": 1.0, "tiers": TIERS, "daily_cap": 20.0}
    res = await grant_engagement_credits(mock_db, user_id=uid, event_id="big", ep=50, now=now, config=cfg)
    assert res["credits"] == pytest.approx(20.0)  # 150 richiesti → cap 20
    # nuovo giorno → cap si resetta
    res2 = await grant_engagement_credits(
        mock_db, user_id=uid, event_id="big2", ep=5, now=now + dt.timedelta(days=1), config=cfg
    )
    assert res2["credits"] > 0


async def test_faucet_independent_of_nackl_ledger(mock_db):
    uid = ObjectId()
    await _wallet(mock_db, uid)
    now = dt.datetime(2026, 1, 1, 12, 0)
    cfg = {"base": 1.0, "tiers": TIERS, "daily_cap": 1_000.0}
    await grant_engagement_credits(mock_db, user_id=uid, event_id="x", ep=10, now=now, config=cfg)
    # NON tocca il ledger NACKL / reward_balances
    assert await mock_db.nackl_ledger.count_documents({}) == 0
    assert await mock_db.reward_balances.count_documents({}) == 0


def test_proposed_config_shape():
    assert [m for _, m in PROPOSED_FAUCET["tiers"]] == [3.0, 1.5, 0.75, 0.2]
    assert PROPOSED_FAUCET["daily_cap"] > 0
    assert PROPOSED_FAUCET["base"] > 0
