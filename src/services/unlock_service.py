from __future__ import annotations

from src.config.unlocks import FEATURE_NAMES, REQUIRED_LEVELS
from src.core.errors import FeatureLockedError
from src.repositories.user_repository import UserRepository


class UnlockService:
    def __init__(self, user_repository: UserRepository, default_coins: int) -> None:
        self.user_repository = user_repository
        self.default_coins = default_coins

    async def require_unlocked(self, user_id: str, feature: str) -> None:
        user = await self.user_repository.get_or_create(user_id, self.default_coins)
        required_level = required_level_for(feature)
        if user.level < required_level:
            raise FeatureLockedError(feature_name_for(feature), required_level)


def required_level_for(feature: str) -> int:
    return REQUIRED_LEVELS.get(feature, 0)


def feature_name_for(feature: str) -> str:
    return FEATURE_NAMES.get(feature, feature.replace("_", " ").title())
