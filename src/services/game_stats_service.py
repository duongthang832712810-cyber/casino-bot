from __future__ import annotations

from dataclasses import dataclass

from src.models.achievement import AchievementDefinition
from src.models.game_stats import GameStats
from src.repositories.game_stats_repository import GameStatsRepository
from src.repositories.user_repository import UserRepository
from src.services.achievement_service import AchievementService


@dataclass(frozen=True, slots=True)
class StatsUpdateResult:
    stats: GameStats
    achievements: list[AchievementDefinition]


class GameStatsService:
    def __init__(self, stats: GameStatsRepository, users: UserRepository, achievements: AchievementService) -> None:
        self.stats = stats
        self.users = users
        self.achievements = achievements

    async def record_result(self, user_id: str, game_type: str, result: str, bet_amount: int, payout: int) -> StatsUpdateResult:
        stats = await self.stats.record_result(user_id, game_type, result, bet_amount, payout)
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise RuntimeError("User not found after stats update")
        achievements = await self.achievements.check_and_unlock(user, stats)
        return StatsUpdateResult(stats=stats, achievements=achievements)

    async def list_by_user(self, user_id: str) -> list[GameStats]:
        return await self.stats.list_by_user(user_id)
