"""RED→GREEN: provider reward (internal placeholder, testnet inerte, factory)."""
from __future__ import annotations

from bson import ObjectId

from app.models.common import utc_now
from app.reward.base import RewardProvider
from app.reward.factory import get_reward_provider
from app.reward.internal import InternalRewardProvider
from app.reward.testnet import TestnetWalletRewardProvider


async def test_internal_accrue_and_balance(mock_db):
    uid = ObjectId()
    p = InternalRewardProvider()
    assert p.is_placeholder is True
    now = utc_now()
    await p.accrue(mock_db, uid, amount=5.0, reason="heartbeat", now=now)
    await p.accrue(mock_db, uid, amount=3.0, reason="heartbeat", now=now)
    bal = await p.balance(mock_db, uid)
    assert bal["amount"] == 5.0 + 3.0
    assert bal["is_placeholder"] is True
    assert bal["currency"] == "NACKL"
    # ledger immutabile: 2 righe
    assert await mock_db.nackl_ledger.count_documents({"user_id": uid}) == 2


async def test_internal_balance_zero_for_new_user(mock_db):
    p = InternalRewardProvider()
    bal = await p.balance(mock_db, ObjectId())
    assert bal["amount"] == 0.0
    assert bal["is_placeholder"] is True


async def test_testnet_is_inert_without_credentials(mock_db):
    """Senza app_id/endpoint (Q1/Q5) il provider testnet è un no-op robusto."""
    p = TestnetWalletRewardProvider(app_id="", graphql_endpoint="")
    assert p.is_placeholder is False  # rappresenta NACKL reale (on-chain)
    bal = await p.balance(mock_db, ObjectId())
    assert bal["amount"] == 0.0
    assert bal["status"] == "pending_credentials"
    # l'app NON emette NACKL reale: accrue non accredita nulla
    assert await p.can_earn(mock_db, ObjectId(), now=utc_now()) is False


async def test_factory_selects_provider():
    class S:
        REWARD_PROVIDER = "internal"
        AN_APP_ID = ""
        AN_GRAPHQL_ENDPOINT = ""
        AN_NETWORK = "shellnet"
    assert isinstance(get_reward_provider(S()), InternalRewardProvider)
    S.REWARD_PROVIDER = "testnet"
    assert isinstance(get_reward_provider(S()), TestnetWalletRewardProvider)


def test_providers_are_reward_providers():
    assert isinstance(InternalRewardProvider(), RewardProvider)
    assert isinstance(TestnetWalletRewardProvider(app_id="", graphql_endpoint=""), RewardProvider)
