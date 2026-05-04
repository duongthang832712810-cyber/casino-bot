from __future__ import annotations

from math import floor

from src.config import mining as mining_config
from src.games.mining.models import MiningComputer


def price_for_tier(tier: int, owned_same_tier: int) -> int:
    base_price = mining_config.TIER_CONFIGS[tier]["base_price"]
    return floor(base_price * (mining_config.PRICE_MULTIPLIER_PER_OWNED_COMPUTER ** owned_same_tier))


def storage_income_for_tier(tier: int) -> int:
    daily_income = mining_config.TIER_CONFIGS[tier]["daily_income"]
    return floor(daily_income * mining_config.MAX_ACCUMULATION_SECONDS / mining_config.SECONDS_PER_DAY)


def stored_seconds_for_computer(computer: MiningComputer, now: int) -> int:
    return max(0, min(now - computer.last_claimed_at, mining_config.MAX_ACCUMULATION_SECONDS))


def income_for_computer(computer: MiningComputer, now: int) -> int:
    elapsed = stored_seconds_for_computer(computer, now)
    daily_income = mining_config.TIER_CONFIGS[computer.tier]["daily_income"]
    return floor(daily_income * elapsed / mining_config.SECONDS_PER_DAY)
