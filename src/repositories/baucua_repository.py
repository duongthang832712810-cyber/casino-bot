from __future__ import annotations

import time

from aiosqlite import Row

from src.db.connection import Database
from src.games.baucua.constants import STATUS_BETTING, STATUS_RESOLVED
from src.games.baucua.models import BaucuaAnnouncement, BaucuaBet, BaucuaState


def _row_to_state(row: Row) -> BaucuaState:
    return BaucuaState(
        round_id=row["round_id"],
        status=row["status"],
        started_at=row["started_at"],
        ends_at=row["ends_at"],
        channel_id=row["channel_id"],
        message_id=row["message_id"],
        result_1=row["result_1"],
        result_2=row["result_2"],
        result_3=row["result_3"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_announcement(row: Row) -> BaucuaAnnouncement:
    return BaucuaAnnouncement(
        guild_id=row["guild_id"],
        channel_id=row["channel_id"],
        message_id=row["message_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_bet(row: Row) -> BaucuaBet:
    return BaucuaBet(
        bet_id=row["bet_id"],
        round_id=row["round_id"],
        user_id=row["user_id"],
        choice=row["choice"],
        amount=row["amount"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class BaucuaRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_state(self) -> BaucuaState | None:
        async with self.db.get_connection().execute("SELECT * FROM baucua_state WHERE id = 1") as cursor:
            row = await cursor.fetchone()
        return _row_to_state(row) if row else None

    async def create_state(self, started_at: int, ends_at: int) -> BaucuaState:
        now = int(time.time())
        await self.db.get_connection().execute(
            """
            INSERT INTO baucua_state (id, round_id, status, started_at, ends_at, created_at, updated_at)
            VALUES (1, 1, ?, ?, ?, ?, ?)
            """,
            (STATUS_BETTING, started_at, ends_at, now, now),
        )
        state = await self.get_state()
        if state is None:
            raise RuntimeError("Failed to create Baucua state")
        return state

    async def get_announcement(self, guild_id: str) -> BaucuaAnnouncement | None:
        async with self.db.get_connection().execute(
            "SELECT * FROM baucua_announcements WHERE guild_id = ?",
            (guild_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return _row_to_announcement(row) if row else None

    async def list_announcements(self) -> list[BaucuaAnnouncement]:
        async with self.db.get_connection().execute("SELECT * FROM baucua_announcements ORDER BY guild_id") as cursor:
            rows = await cursor.fetchall()
        return [_row_to_announcement(row) for row in rows]

    async def upsert_announcement(self, guild_id: str, channel_id: str, message_id: str | None) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            """
            INSERT INTO baucua_announcements (guild_id, channel_id, message_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                channel_id = excluded.channel_id,
                message_id = excluded.message_id,
                updated_at = excluded.updated_at
            """,
            (guild_id, channel_id, message_id, now, now),
        )

    async def update_announcement_message(self, guild_id: str, message_id: str | None) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            "UPDATE baucua_announcements SET message_id = ?, updated_at = ? WHERE guild_id = ?",
            (message_id, now, guild_id),
        )

    async def get_user_choice_bet(self, round_id: int, user_id: str, choice: str) -> BaucuaBet | None:
        async with self.db.get_connection().execute(
            "SELECT * FROM baucua_bets WHERE round_id = ? AND user_id = ? AND choice = ?",
            (round_id, user_id, choice),
        ) as cursor:
            row = await cursor.fetchone()
        return _row_to_bet(row) if row else None

    async def add_bet(self, round_id: int, user_id: str, choice: str, amount: int) -> BaucuaBet:
        now = int(time.time())
        existing = await self.get_user_choice_bet(round_id, user_id, choice)
        if existing is not None:
            await self.db.get_connection().execute(
                "UPDATE baucua_bets SET amount = amount + ?, updated_at = ? WHERE bet_id = ?",
                (amount, now, existing.bet_id),
            )
            bet = await self.get_user_choice_bet(round_id, user_id, choice)
            if bet is None:
                raise RuntimeError("Failed to update Baucua bet")
            return bet

        cursor = await self.db.get_connection().execute(
            """
            INSERT INTO baucua_bets (round_id, user_id, choice, amount, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (round_id, user_id, choice, amount, now, now),
        )
        bet_id = cursor.lastrowid
        async with self.db.get_connection().execute("SELECT * FROM baucua_bets WHERE bet_id = ?", (bet_id,)) as read_cursor:
            row = await read_cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to create Baucua bet")
        return _row_to_bet(row)

    async def list_bets(self, round_id: int) -> list[BaucuaBet]:
        async with self.db.get_connection().execute(
            "SELECT * FROM baucua_bets WHERE round_id = ? ORDER BY bet_id",
            (round_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [_row_to_bet(row) for row in rows]

    async def finish_round(self, results: tuple[str, str, str]) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            """
            UPDATE baucua_state
            SET status = ?, result_1 = ?, result_2 = ?, result_3 = ?, updated_at = ?
            WHERE id = 1
            """,
            (STATUS_RESOLVED, results[0], results[1], results[2], now),
        )

    async def start_next_round(self, started_at: int, ends_at: int) -> BaucuaState:
        now = int(time.time())
        await self.db.get_connection().execute(
            """
            UPDATE baucua_state
            SET round_id = round_id + 1,
                status = ?,
                started_at = ?,
                ends_at = ?,
                message_id = NULL,
                result_1 = NULL,
                result_2 = NULL,
                result_3 = NULL,
                updated_at = ?
            WHERE id = 1
            """,
            (STATUS_BETTING, started_at, ends_at, now),
        )
        state = await self.get_state()
        if state is None:
            raise RuntimeError("Failed to start next Baucua round")
        return state

    async def delete_old_bets(self, round_id: int) -> None:
        await self.db.get_connection().execute("DELETE FROM baucua_bets WHERE round_id < ?", (round_id,))
