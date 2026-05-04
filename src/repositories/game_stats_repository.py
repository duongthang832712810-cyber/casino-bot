from __future__ import annotations

import time

from aiosqlite import Row

from src.core.constants import RESULT_BLACKJACK, RESULT_DRAW, RESULT_LOSE, RESULT_WIN
from src.db.connection import Database
from src.models.game_stats import GameStats


def _row_to_stats(row: Row) -> GameStats:
    return GameStats(
        user_id=row["user_id"],
        game_type=row["game_type"],
        wins=row["wins"],
        losses=row["losses"],
        draws=row["draws"],
        total_games=row["total_games"],
        current_win_streak=row["current_win_streak"],
        current_loss_streak=row["current_loss_streak"],
        best_win_streak=row["best_win_streak"],
        best_loss_streak=row["best_loss_streak"],
        total_bet=row["total_bet"],
        total_payout=row["total_payout"],
        net_profit=row["net_profit"],
        biggest_bet=row["biggest_bet"],
        biggest_win=row["biggest_win"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class GameStatsRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get(self, user_id: str, game_type: str) -> GameStats | None:
        async with self.db.get_connection().execute(
            "SELECT * FROM user_game_stats WHERE user_id = ? AND game_type = ?",
            (user_id, game_type),
        ) as cursor:
            row = await cursor.fetchone()
        return _row_to_stats(row) if row else None

    async def list_by_user(self, user_id: str) -> list[GameStats]:
        async with self.db.get_connection().execute(
            "SELECT * FROM user_game_stats WHERE user_id = ? ORDER BY game_type",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [_row_to_stats(row) for row in rows]

    async def ensure(self, user_id: str, game_type: str) -> GameStats:
        existing = await self.get(user_id, game_type)
        if existing is not None:
            return existing
        now = int(time.time())
        await self.db.get_connection().execute(
            """
            INSERT INTO user_game_stats (
                user_id, game_type, wins, losses, draws, total_games,
                current_win_streak, current_loss_streak, best_win_streak, best_loss_streak,
                total_bet, total_payout, net_profit, biggest_bet, biggest_win,
                created_at, updated_at
            ) VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ?, ?)
            ON CONFLICT(user_id, game_type) DO NOTHING
            """,
            (user_id, game_type, now, now),
        )
        stats = await self.get(user_id, game_type)
        if stats is None:
            raise RuntimeError("Failed to create game stats")
        return stats

    async def record_result(self, user_id: str, game_type: str, result: str, bet_amount: int, payout: int) -> GameStats:
        stats = await self.ensure(user_id, game_type)
        win_inc = 1 if result in {RESULT_WIN, RESULT_BLACKJACK} else 0
        loss_inc = 1 if result == RESULT_LOSE else 0
        draw_inc = 1 if result == RESULT_DRAW else 0
        current_win_streak = stats.current_win_streak + 1 if win_inc else 0
        current_loss_streak = stats.current_loss_streak + 1 if loss_inc else 0
        best_win_streak = max(stats.best_win_streak, current_win_streak)
        best_loss_streak = max(stats.best_loss_streak, current_loss_streak)
        biggest_win = max(stats.biggest_win, max(0, payout - bet_amount))
        biggest_bet = max(stats.biggest_bet, bet_amount)
        now = int(time.time())
        await self.db.get_connection().execute(
            """
            UPDATE user_game_stats
            SET wins = wins + ?,
                losses = losses + ?,
                draws = draws + ?,
                total_games = total_games + 1,
                current_win_streak = ?,
                current_loss_streak = ?,
                best_win_streak = ?,
                best_loss_streak = ?,
                total_bet = total_bet + ?,
                total_payout = total_payout + ?,
                net_profit = net_profit + ?,
                biggest_bet = ?,
                biggest_win = ?,
                updated_at = ?
            WHERE user_id = ? AND game_type = ?
            """,
            (
                win_inc,
                loss_inc,
                draw_inc,
                current_win_streak,
                current_loss_streak,
                best_win_streak,
                best_loss_streak,
                bet_amount,
                payout,
                payout - bet_amount,
                biggest_bet,
                biggest_win,
                now,
                user_id,
                game_type,
            ),
        )
        updated = await self.get(user_id, game_type)
        if updated is None:
            raise RuntimeError("Failed to update game stats")
        return updated

    async def top(self, category: str, game_type: str | None, limit: int) -> list[tuple[str, int]]:
        column = {
            "wins": "wins",
            "profit": "net_profit",
            "bet": "total_bet",
        }.get(category)
        if column is None:
            return []
        if game_type:
            query = f"SELECT user_id, {column} AS value FROM user_game_stats WHERE game_type = ? ORDER BY {column} DESC, user_id ASC LIMIT ?"
            params = (game_type, limit)
        else:
            query = f"SELECT user_id, SUM({column}) AS value FROM user_game_stats GROUP BY user_id ORDER BY value DESC, user_id ASC LIMIT ?"
            params = (limit,)
        async with self.db.get_connection().execute(query, params) as cursor:
            rows = await cursor.fetchall()
        return [(row["user_id"], int(row["value"] or 0)) for row in rows]
