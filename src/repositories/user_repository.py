from __future__ import annotations

import time

from aiosqlite import Row

from src.db.connection import Database
from src.models.user import User


def _row_to_user(row: Row) -> User:
    return User(
        user_id=row["user_id"],
        coins=row["coins"],
        exp=row["exp"],
        wins=row["wins"],
        losses=row["losses"],
        draws=row["draws"],
        total_games=row["total_games"],
        has_game=bool(row["has_game"]),
        active_game_type=row["active_game_type"],
        daily_claimed_at=row["daily_claimed_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class UserRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        conn = self.db.get_connection()
        async with conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
        return _row_to_user(row) if row else None

    async def create(self, user_id: str, default_coins: int) -> User:
        now = int(time.time())
        conn = self.db.get_connection()
        await conn.execute(
            """
            INSERT INTO users (user_id, coins, exp, wins, losses, draws, total_games, has_game, active_game_type, daily_claimed_at, created_at, updated_at)
            VALUES (?, ?, 0, 0, 0, 0, 0, 0, NULL, 0, ?, ?)
            """,
            (user_id, default_coins, now, now),
        )
        await conn.commit()
        user = await self.get_by_id(user_id)
        if user is None:
            raise RuntimeError("Failed to create user")
        return user

    async def get_or_create(self, user_id: str, default_coins: int) -> User:
        user = await self.get_by_id(user_id)
        if user is not None:
            return user
        return await self.create(user_id, default_coins)

    async def set_active_game(self, user_id: str, game_type: str | None) -> None:
        now = int(time.time())
        has_game = 1 if game_type else 0
        conn = self.db.get_connection()
        await conn.execute(
            "UPDATE users SET has_game = ?, active_game_type = ?, updated_at = ? WHERE user_id = ?",
            (has_game, game_type, now, user_id),
        )

    async def update_after_result(self, user_id: str, payout: int, exp_delta: int, result: str) -> None:
        now = int(time.time())
        win_inc = 1 if result in {"win", "blackjack"} else 0
        loss_inc = 1 if result == "lose" else 0
        draw_inc = 1 if result == "draw" else 0
        conn = self.db.get_connection()
        await conn.execute(
            """
            UPDATE users
            SET coins = MAX(0, coins + ?),
                exp = MAX(0, exp + ?),
                wins = wins + ?,
                losses = losses + ?,
                draws = draws + ?,
                total_games = total_games + 1,
                has_game = 0,
                active_game_type = NULL,
                updated_at = ?
            WHERE user_id = ?
            """,
            (payout, exp_delta, win_inc, loss_inc, draw_inc, now, user_id),
        )

    async def add_coins(self, user_id: str, amount: int) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            "UPDATE users SET coins = MAX(0, coins + ?), updated_at = ? WHERE user_id = ?",
            (amount, now, user_id),
        )

    async def claim_daily_reward(self, user_id: str, reward: int, claimed_at: int) -> None:
        await self.db.get_connection().execute(
            """
            UPDATE users
            SET coins = coins + ?, daily_claimed_at = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (reward, claimed_at, claimed_at, user_id),
        )
