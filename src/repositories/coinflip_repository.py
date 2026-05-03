from __future__ import annotations

import time

from aiosqlite import Row

from src.db.connection import Database
from src.games.coinflip.models import CoinFlipGame


def _row_to_game(row: Row) -> CoinFlipGame:
    return CoinFlipGame(
        user_id=row["user_id"],
        bet_amount=row["bet_amount"],
        choice=row["choice"],
        resolve_at=row["resolve_at"],
        channel_id=row["channel_id"],
        message_id=row["message_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class CoinFlipRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_by_user_id(self, user_id: str) -> CoinFlipGame | None:
        conn = self.db.get_connection()
        async with conn.execute("SELECT * FROM coinflip_games WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
        return _row_to_game(row) if row else None

    async def list_pending(self) -> list[CoinFlipGame]:
        conn = self.db.get_connection()
        async with conn.execute("SELECT * FROM coinflip_games") as cursor:
            rows = await cursor.fetchall()
        return [_row_to_game(row) for row in rows]

    async def create(self, game: CoinFlipGame) -> None:
        now = int(time.time())
        game.created_at = now
        game.updated_at = now
        conn = self.db.get_connection()
        await conn.execute(
            """
            INSERT INTO coinflip_games (user_id, bet_amount, choice, resolve_at, channel_id, message_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                game.user_id,
                game.bet_amount,
                game.choice,
                game.resolve_at,
                game.channel_id,
                game.message_id,
                now,
                now,
            ),
        )

    async def save_message(self, user_id: str, channel_id: str | None, message_id: str | None) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            "UPDATE coinflip_games SET channel_id = ?, message_id = ?, updated_at = ? WHERE user_id = ?",
            (channel_id, message_id, now, user_id),
        )

    async def delete(self, user_id: str) -> None:
        await self.db.get_connection().execute("DELETE FROM coinflip_games WHERE user_id = ?", (user_id,))
