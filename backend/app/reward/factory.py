"""Selezione del RewardProvider da settings (REWARD_PROVIDER=internal|testnet)."""
from __future__ import annotations

from app.reward.base import RewardProvider
from app.reward.internal import InternalRewardProvider
from app.reward.testnet import TestnetWalletRewardProvider


def get_reward_provider(settings) -> RewardProvider:
    if settings.REWARD_PROVIDER == "testnet":
        return TestnetWalletRewardProvider(
            app_id=getattr(settings, "AN_APP_ID", ""),
            graphql_endpoint=getattr(settings, "AN_GRAPHQL_ENDPOINT", ""),
            network=getattr(settings, "AN_NETWORK", "shellnet"),
        )
    return InternalRewardProvider()
