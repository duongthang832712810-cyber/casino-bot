from __future__ import annotations

import time

from aiosqlite import Row

from src.core.constants import RESULT_BLACKJACK, RESULT_DRAW, RESULT_LOSE, RESULT_WIN
from src.db.connection import Database
from src.models.user import User
from src.services.progression_service import ProgressionService, ProgressionUpdate


def _row_to_user(row: Row) -> User:
    return User(
        user_id=row["user_id"],
        coins=row["coins"],
        exp=row["exp"],
        level=row["level"],
        wins=row["wins"],
        losses=row["losses"],
        draws=row["draws"],
        total_games=row["total_games"],
        total_bet=row["total_bet"],
        total_payout=row["total_payout"],
        net_profit=row["net_profit"],
        achievements_unlocked=row["achievements_unlocked"],
        current_win_streak=row["current_win_streak"],
        current_loss_streak=row["current_loss_streak"],
        best_win_streak=row["best_win_streak"],
        best_loss_streak=row["best_loss_streak"],
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
            INSERT INTO users (
                user_id, coins, exp, level, wins, losses, draws, total_games,
                total_bet, total_payout, net_profit, achievements_unlocked,
                current_win_streak, current_loss_streak, best_win_streak, best_loss_streak,
                has_game, active_game_type, daily_claimed_at, created_at, updated_at
            ) VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, NULL, 0, ?, ?)
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

    async def update_after_result(
        self,
        user_id: str,
        bet_amount: int,
        payout: int,
        exp_delta: int,
        result: str,
        *,
        clear_active_game: bool = True,
    ) -> ProgressionUpdate:
        now = int(time.time())
        win_inc = 1 if result in {RESULT_WIN, RESULT_BLACKJACK} else 0
        loss_inc = 1 if result == RESULT_LOSE else 0
        draw_inc = 1 if result == RESULT_DRAW else 0
        conn = self.db.get_connection()
        user = await self.get_by_id(user_id)
        if user is None:
            raise RuntimeError("User not found")
        progression = ProgressionService.apply_exp_delta(user.level, user.exp, exp_delta)
        current_win_streak = user.current_win_streak + 1 if win_inc else 0
        current_loss_streak = user.current_loss_streak + 1 if loss_inc else 0
        best_win_streak = max(user.best_win_streak, current_win_streak)
        best_loss_streak = max(user.best_loss_streak, current_loss_streak)
        active_game_sql = ", has_game = 0, active_game_type = NULL" if clear_active_game else ""
        await conn.execute(
            f"""
            UPDATE users
            SET coins = MAX(0, coins + ?),
                exp = ?,
                level = ?,
                wins = wins + ?,
                losses = losses + ?,
                draws = draws + ?,
                total_games = total_games + 1,
                total_bet = total_bet + ?,
                total_payout = total_payout + ?,
                net_profit = net_profit + ?,
                current_win_streak = ?,
                current_loss_streak = ?,
                best_win_streak = ?,
                best_loss_streak = ?
                {active_game_sql},
                updated_at = ?
            WHERE user_id = ?
            """,
            (
                payout,
                progression.new_exp,
                progression.new_level,
                win_inc,
                loss_inc,
                draw_inc,
                bet_amount,
                payout,
                payout - bet_amount,
                current_win_streak,
                current_loss_streak,
                best_win_streak,
                best_loss_streak,
                now,
                user_id,
            ),
        )
        return progression

    async def add_coins(self, user_id: str, amount: int) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            "UPDATE users SET coins = MAX(0, coins + ?), updated_at = ? WHERE user_id = ?",
            (amount, now, user_id),
        )

    async def increment_achievements(self, user_id: str, amount: int) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            "UPDATE users SET achievements_unlocked = achievements_unlocked + ?, updated_at = ? WHERE user_id = ?",
            (amount, now, user_id),
        )

    async def top(self, category: str, limit: int) -> list[tuple[str, int]]:
        column = {
            "coins": "coins",
            "level": "level",
            "wins": "wins",
            "profit": "net_profit",
            "bet": "total_bet",
            "achievements": "achievements_unlocked",
        }.get(category, "coins")
        query = f"SELECT user_id, {column} AS value FROM users ORDER BY {column} DESC, user_id ASC LIMIT ?"
        async with self.db.get_connection().execute(query, (limit,)) as cursor:
            rows = await cursor.fetchall()
        return [(row["user_id"], int(row["value"] or 0)) for row in rows]

    async def claim_daily_reward(self, user_id: str, reward: int, claimed_at: int) -> None:
        await self.db.get_connection().execute(
            """
            UPDATE users
            SET coins = coins + ?, daily_claimed_at = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (reward, claimed_at, claimed_at, user_id),
        )
