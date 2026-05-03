from __future__ import annotations

import json
import time

from aiosqlite import Row

from src.db.connection import Database
from src.games.blackjack.models import BlackjackGame


def _loads(value: str) -> list[str]:
    return list(json.loads(value))


def _row_to_game(row: Row) -> BlackjackGame:
    return BlackjackGame(
        user_id=row["user_id"],
        bet_amount=row["bet_amount"],
        player_cards=_loads(row["player_cards"]),
        dealer_cards=_loads(row["dealer_cards"]),
        deck=_loads(row["deck"]),
        channel_id=row["channel_id"],
        message_id=row["message_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class BlackjackRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_by_user_id(self, user_id: str) -> BlackjackGame | None:
        conn = self.db.get_connection()
        async with conn.execute("SELECT * FROM blackjack_games WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
        return _row_to_game(row) if row else None

    async def create(self, game: BlackjackGame) -> None:
        now = int(time.time())
        game.created_at = now
        game.updated_at = now
        conn = self.db.get_connection()
        await conn.execute(
            """
            INSERT INTO blackjack_games (user_id, bet_amount, player_cards, dealer_cards, deck, channel_id, message_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                game.user_id,
                game.bet_amount,
                json.dumps(game.player_cards),
                json.dumps(game.dealer_cards),
                json.dumps(game.deck),
                game.channel_id,
                game.message_id,
                now,
                now,
            ),
        )

    async def update(self, game: BlackjackGame) -> None:
        now = int(time.time())
        game.updated_at = now
        conn = self.db.get_connection()
        await conn.execute(
            """
            UPDATE blackjack_games
            SET bet_amount = ?, player_cards = ?, dealer_cards = ?, deck = ?, channel_id = ?, message_id = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (
                game.bet_amount,
                json.dumps(game.player_cards),
                json.dumps(game.dealer_cards),
                json.dumps(game.deck),
                game.channel_id,
                game.message_id,
                now,
                game.user_id,
            ),
        )

    async def save_message(self, user_id: str, channel_id: str | None, message_id: str | None) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            "UPDATE blackjack_games SET channel_id = ?, message_id = ?, updated_at = ? WHERE user_id = ?",
            (channel_id, message_id, now, user_id),
        )

    async def delete(self, user_id: str) -> None:
        await self.db.get_connection().execute("DELETE FROM blackjack_games WHERE user_id = ?", (user_id,))
