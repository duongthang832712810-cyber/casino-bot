from __future__ import annotations

import time

from aiosqlite import Row

from src.db.connection import Database
from src.models.achievement import UserAchievement


def _row_to_achievement(row: Row) -> UserAchievement:
    return UserAchievement(
        user_id=row["user_id"],
        achievement_id=row["achievement_id"],
        game_type=row["game_type"],
        unlocked_at=row["unlocked_at"],
    )


class AchievementRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def unlock(self, user_id: str, achievement_id: str, game_type: str | None) -> bool:
        cursor = await self.db.get_connection().execute(
            """
            INSERT OR IGNORE INTO user_achievements (user_id, achievement_id, game_type, unlocked_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, achievement_id, game_type, int(time.time())),
        )
        return cursor.rowcount == 1

    async def list_by_user(self, user_id: str) -> list[UserAchievement]:
        async with self.db.get_connection().execute(
            "SELECT * FROM user_achievements WHERE user_id = ? ORDER BY unlocked_at DESC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [_row_to_achievement(row) for row in rows]

    async def count_by_user(self, user_id: str) -> int:
        async with self.db.get_connection().execute(
            "SELECT COUNT(*) AS count FROM user_achievements WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return int(row["count"] if row else 0)
