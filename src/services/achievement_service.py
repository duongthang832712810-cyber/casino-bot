from __future__ import annotations

from src.config.achievements import ACHIEVEMENTS, GLOBAL_ACHIEVEMENTS, PER_GAME_ACHIEVEMENTS
from src.models.achievement import AchievementDefinition, UserAchievement
from src.models.game_stats import GameStats
from src.models.user import User
from src.repositories.achievement_repository import AchievementRepository
from src.repositories.user_repository import UserRepository


class AchievementService:
    def __init__(self, achievements: AchievementRepository, users: UserRepository) -> None:
        self.achievements = achievements
        self.users = users

    async def check_and_unlock(self, user: User, game_stats: GameStats) -> list[AchievementDefinition]:
        unlocked: list[AchievementDefinition] = []
        for definition in GLOBAL_ACHIEVEMENTS:
            if self._is_unlocked(definition, user, game_stats):
                if await self.achievements.unlock(user.user_id, definition.achievement_id, None):
                    await self.users.increment_achievements(user.user_id, 1)
                    unlocked.append(definition)
        for definition in PER_GAME_ACHIEVEMENTS:
            if definition.game_type != game_stats.game_type:
                continue
            if self._is_unlocked(definition, user, game_stats):
                if await self.achievements.unlock(user.user_id, definition.achievement_id, definition.game_type):
                    await self.users.increment_achievements(user.user_id, 1)
                    unlocked.append(definition)
        return unlocked

    async def list_user_achievements(self, user_id: str) -> list[UserAchievement]:
        return await self.achievements.list_by_user(user_id)

    @staticmethod
    def definition(achievement_id: str) -> AchievementDefinition | None:
        return ACHIEVEMENTS.get(achievement_id)

    @staticmethod
    def total_count() -> int:
        return len(ACHIEVEMENTS)

    @staticmethod
    def game_count(game_type: str | None) -> int:
        return sum(1 for definition in ACHIEVEMENTS.values() if definition.game_type == game_type)

    @staticmethod
    def _is_unlocked(definition: AchievementDefinition, user: User, stats: GameStats) -> bool:
        source = user if definition.game_type is None else stats
        return int(getattr(source, definition.condition, 0)) >= definition.target


def format_achievement_unlocks(user_id: str, achievements: list[AchievementDefinition]) -> str | None:
    if not achievements:
        return None
    lines = [f"<@{user_id}> unlocked **{achievement.name}**!" for achievement in achievements]
    return "\n".join(lines)
