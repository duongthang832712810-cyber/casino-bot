from __future__ import annotations

from src.config import mining as mining_config
from src.core.errors import (
    InvalidBetAmountError,
    MiningClaimCooldownError,
    MiningComputerLimitError,
    MiningNoComputerError,
    MiningNoStoredCoinsError,
    NotEnoughCoinsError,
)
from src.db.connection import Database
from src.db.transaction import immediate_transaction
from src.games.mining.calculations import (
    income_for_computer,
    price_for_tier,
    storage_income_for_tier,
    stored_seconds_for_computer,
)
from src.games.mining.models import MiningComputer, MiningClaimResult, MiningComputerSummary, MiningPurchaseResult, MiningShopTier
from src.repositories.mining_repository import MiningRepository
from src.repositories.user_repository import UserRepository
from src.utils.money import format_coin, format_number
from src.utils.time import format_duration, utc_timestamp


class MiningService:
    def __init__(self, db: Database, users: UserRepository, mining: MiningRepository, default_coins: int) -> None:
        self.db = db
        self.users = users
        self.mining = mining
        self.default_coins = default_coins

    async def shop(self, user_id: str) -> list[MiningShopTier]:
        await self.users.get_or_create(user_id, self.default_coins)
        owned_by_tier = await self.mining.count_by_tier(user_id)
        return [
            MiningShopTier(
                tier=tier,
                base_price=config["base_price"],
                next_price=price_for_tier(tier, owned_by_tier.get(tier, 0)),
                daily_income=config["daily_income"],
                storage_income=storage_income_for_tier(tier),
                owned=owned_by_tier.get(tier, 0),
            )
            for tier, config in mining_config.TIER_CONFIGS.items()
        ]

    async def buy(self, user_id: str, tier: int) -> MiningPurchaseResult:
        self._validate_tier(tier)
        await self.users.get_or_create(user_id, self.default_coins)

        async with immediate_transaction(self.db):
            user = await self.users.get_by_id(user_id)
            if user is None:
                raise RuntimeError("User disappeared")
            total_computers = await self.mining.count_computers(user_id)
            if total_computers >= mining_config.MAX_COMPUTERS_PER_USER:
                raise MiningComputerLimitError(
                    f"You can own up to {format_number(mining_config.MAX_COMPUTERS_PER_USER)} Lucky Mining computers."
                )
            owned_same_tier = await self.mining.count_computers_by_tier(user_id, tier)
            price = price_for_tier(tier, owned_same_tier)
            if user.coins < price:
                raise NotEnoughCoinsError("Not enough coins to buy this Lucky Mining computer.")

            now = utc_timestamp()
            await self.users.add_coins(user_id, -price)
            await self.mining.create_computer(user_id, tier, price, now)
            await self.mining.record_purchase(user_id, tier, now)

        return MiningPurchaseResult(tier=tier, price=price, total_computers=total_computers + 1)

    async def list_computers(self, user_id: str) -> list[MiningComputer]:
        await self.users.get_or_create(user_id, self.default_coins)
        return await self.mining.list_computers(user_id)

    async def summaries(self, user_id: str) -> list[MiningComputerSummary]:
        computers = await self.list_computers(user_id)
        now = utc_timestamp()
        summaries: list[MiningComputerSummary] = []
        for computer in computers:
            daily_income = mining_config.TIER_CONFIGS[computer.tier]["daily_income"]
            stored_seconds = stored_seconds_for_computer(computer, now)
            stored_income = income_for_computer(computer, now)
            remaining_storage_seconds = max(0, mining_config.MAX_ACCUMULATION_SECONDS - stored_seconds)
            summaries.append(
                MiningComputerSummary(
                    computer.tier,
                    1,
                    daily_income,
                    stored_income,
                    stored_seconds,
                    remaining_storage_seconds,
                )
            )
        return summaries

    async def claim(self, user_id: str) -> MiningClaimResult:
        await self.users.get_or_create(user_id, self.default_coins)
        now = utc_timestamp()
        async with immediate_transaction(self.db):
            stats = await self.mining.ensure_stats(user_id)
            if stats.last_claimed_at and now - stats.last_claimed_at < mining_config.CLAIM_COOLDOWN_SECONDS:
                retry_after = mining_config.CLAIM_COOLDOWN_SECONDS - (now - stats.last_claimed_at)
                raise MiningClaimCooldownError(
                    retry_after,
                    f"You can claim mined coins again in {format_duration(retry_after)}.",
                )

            computers = await self.mining.list_computers(user_id)
            if not computers:
                raise MiningNoComputerError("You do not own any Lucky Mining computers yet.")

            claimed = sum(income_for_computer(computer, now) for computer in computers)
            if claimed <= 0:
                raise MiningNoStoredCoinsError("Your Lucky Mining computers have not generated enough coins to claim yet.")

            await self.users.add_coins(user_id, claimed)
            await self.mining.update_all_claimed(user_id, now)
            await self.mining.record_claim(user_id, claimed, now)

        return MiningClaimResult(
            claimed=claimed,
            computer_count=len(computers),
            next_claim_at=now + mining_config.CLAIM_COOLDOWN_SECONDS,
        )

    @staticmethod
    def _validate_tier(tier: int) -> None:
        if tier < mining_config.TIER_MIN or tier > mining_config.TIER_MAX:
            raise InvalidBetAmountError(
                f"Mining tier must be between {format_number(mining_config.TIER_MIN)} and {format_number(mining_config.TIER_MAX)}."
            )
