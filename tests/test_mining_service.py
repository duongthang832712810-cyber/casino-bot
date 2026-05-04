from __future__ import annotations

from src.config import mining as mining_config
from src.games.mining.calculations import income_for_computer, price_for_tier, storage_income_for_tier
from src.games.mining.models import MiningComputer


def test_price_increases_only_by_same_tier_owned_count() -> None:
    assert price_for_tier(1, 0) == mining_config.TIER_CONFIGS[1]["base_price"]
    assert price_for_tier(1, 1) == int(mining_config.TIER_CONFIGS[1]["base_price"] * 1.5)
    assert price_for_tier(7, 2) == int(mining_config.TIER_CONFIGS[7]["base_price"] * 1.5**2)


def test_storage_income_uses_configured_cap() -> None:
    expected = int(
        mining_config.TIER_CONFIGS[1]["daily_income"]
        * mining_config.MAX_ACCUMULATION_SECONDS
        / mining_config.SECONDS_PER_DAY
    )
    assert storage_income_for_tier(1) == expected


def test_income_uses_real_elapsed_time_and_storage_cap() -> None:
    computer = MiningComputer(
        computer_id=1,
        user_id="123",
        tier=1,
        purchase_price=25000,
        purchased_at=1000,
        last_claimed_at=1000,
        created_at=1000,
        updated_at=1000,
    )

    one_hour_income = income_for_computer(computer, 4600)
    capped_income = income_for_computer(computer, 1000 + mining_config.MAX_ACCUMULATION_SECONDS + 3600)

    assert one_hour_income == int(mining_config.TIER_CONFIGS[1]["daily_income"] * 3600 / mining_config.SECONDS_PER_DAY)
    assert capped_income == storage_income_for_tier(1)
