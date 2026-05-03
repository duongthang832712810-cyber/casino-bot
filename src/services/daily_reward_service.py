from __future__ import annotations

import time
from dataclasses import dataclass

from src.core.errors import DailyRewardCooldownError
from src.db.connection import Database
from src.db.transaction import immediate_transaction
from src.repositories.user_repository import UserRepository


@dataclass(frozen=True, slots=True)
class DailyRewardClaim:
    reward: int
    new_balance: int
    claimed_at: int


class DailyRewardService:
    def __init__(
        self,
        db: Database,
        users: UserRepository,
        default_coins: int,
        reward: int,
        cooldown_seconds: int,
    ) -> None:
        self.db = db
        self.users = users
        self.default_coins = default_coins
        self.reward = reward
        self.cooldown_seconds = cooldown_seconds

    async def claim(self, user_id: str) -> DailyRewardClaim:
        await self.users.get_or_create(user_id, self.default_coins)

        now = int(time.time())
        async with immediate_transaction(self.db):
            user = await self.users.get_by_id(user_id)
            if user is None:
                raise RuntimeError("Failed to load user for daily reward.")

            elapsed = now - user.daily_claimed_at
            if user.daily_claimed_at > 0 and elapsed < self.cooldown_seconds:
                raise DailyRewardCooldownError(self.cooldown_seconds - elapsed)

            await self.users.claim_daily_reward(user_id, self.reward, now)
            return DailyRewardClaim(
                reward=self.reward,
                new_balance=user.coins + self.reward,
                claimed_at=now,
            )
