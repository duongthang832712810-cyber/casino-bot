from __future__ import annotations

from src.config import leaderboard as leaderboard_config
from src.repositories.game_stats_repository import GameStatsRepository
from src.repositories.user_repository import UserRepository


class LeaderboardService:
    def __init__(self, users: UserRepository, game_stats: GameStatsRepository) -> None:
        self.users = users
        self.game_stats = game_stats

    async def top(self, category: str, game_type: str | None = None) -> list[tuple[str, int]]:
        category = category.lower().strip()
        if category in {leaderboard_config.CATEGORY_COINS, leaderboard_config.CATEGORY_LEVEL, leaderboard_config.CATEGORY_ACHIEVEMENTS}:
            return await self.users.top(category, leaderboard_config.LEADERBOARD_LIMIT)
        if category in {leaderboard_config.CATEGORY_WINS, leaderboard_config.CATEGORY_PROFIT, leaderboard_config.CATEGORY_BET}:
            if game_type in {"", "all", None}:
                return await self.users.top(category, leaderboard_config.LEADERBOARD_LIMIT)
            return await self.game_stats.top(category, game_type, leaderboard_config.LEADERBOARD_LIMIT)
        return await self.users.top(leaderboard_config.CATEGORY_COINS, leaderboard_config.LEADERBOARD_LIMIT)
