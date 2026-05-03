from __future__ import annotations

import time

from aiosqlite import Row

from src.db.connection import Database
from src.games.sicbo.constants import STATUS_BETTING, STATUS_RESOLVED
from src.games.sicbo.models import SicboAnnouncement, SicboBet, SicboState


def _row_to_state(row: Row) -> SicboState:
    return SicboState(
        round_id=row["round_id"],
        status=row["status"],
        started_at=row["started_at"],
        ends_at=row["ends_at"],
        channel_id=row["channel_id"],
        message_id=row["message_id"],
        result=row["result"],
        dice_1=row["dice_1"],
        dice_2=row["dice_2"],
        dice_3=row["dice_3"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_announcement(row: Row) -> SicboAnnouncement:
    return SicboAnnouncement(
        guild_id=row["guild_id"],
        channel_id=row["channel_id"],
        message_id=row["message_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_bet(row: Row) -> SicboBet:
    return SicboBet(
        bet_id=row["bet_id"],
        round_id=row["round_id"],
        user_id=row["user_id"],
        choice=row["choice"],
        amount=row["amount"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class SicboRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_state(self) -> SicboState | None:
        async with self.db.get_connection().execute("SELECT * FROM sicbo_state WHERE id = 1") as cursor:
            row = await cursor.fetchone()
        return _row_to_state(row) if row else None

    async def create_state(self, started_at: int, ends_at: int) -> SicboState:
        now = int(time.time())
        await self.db.get_connection().execute(
            """
            INSERT INTO sicbo_state (
                id, round_id, status, started_at, ends_at, created_at, updated_at
            ) VALUES (1, 1, ?, ?, ?, ?, ?)
            """,
            (STATUS_BETTING, started_at, ends_at, now, now),
        )
        state = await self.get_state()
        if state is None:
            raise RuntimeError("Failed to create Sicbo state")
        return state

    async def update_channel_and_message(self, channel_id: str | None, message_id: str | None) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            "UPDATE sicbo_state SET channel_id = ?, message_id = ?, updated_at = ? WHERE id = 1",
            (channel_id, message_id, now),
        )

    async def update_message(self, message_id: str | None) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            "UPDATE sicbo_state SET message_id = ?, updated_at = ? WHERE id = 1",
            (message_id, now),
        )

    async def get_announcement(self, guild_id: str) -> SicboAnnouncement | None:
        async with self.db.get_connection().execute(
            "SELECT * FROM sicbo_announcements WHERE guild_id = ?",
            (guild_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return _row_to_announcement(row) if row else None

    async def list_announcements(self) -> list[SicboAnnouncement]:
        async with self.db.get_connection().execute(
            "SELECT * FROM sicbo_announcements ORDER BY guild_id"
        ) as cursor:
            rows = await cursor.fetchall()
        return [_row_to_announcement(row) for row in rows]

    async def upsert_announcement(self, guild_id: str, channel_id: str, message_id: str | None) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            """
            INSERT INTO sicbo_announcements (guild_id, channel_id, message_id, created_at, updated_at)
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
            "UPDATE sicbo_announcements SET message_id = ?, updated_at = ? WHERE guild_id = ?",
            (message_id, now, guild_id),
        )

    async def get_user_bet(self, round_id: int, user_id: str) -> SicboBet | None:
        async with self.db.get_connection().execute(
            "SELECT * FROM sicbo_bets WHERE round_id = ? AND user_id = ?",
            (round_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
        return _row_to_bet(row) if row else None

    async def add_bet(self, round_id: int, user_id: str, choice: str, amount: int) -> SicboBet:
        now = int(time.time())
        cursor = await self.db.get_connection().execute(
            """
            INSERT INTO sicbo_bets (round_id, user_id, choice, amount, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (round_id, user_id, choice, amount, now, now),
        )
        bet_id = cursor.lastrowid
        async with self.db.get_connection().execute("SELECT * FROM sicbo_bets WHERE bet_id = ?", (bet_id,)) as read_cursor:
            row = await read_cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to create Sicbo bet")
        return _row_to_bet(row)

    async def list_bets(self, round_id: int) -> list[SicboBet]:
        async with self.db.get_connection().execute(
            "SELECT * FROM sicbo_bets WHERE round_id = ? ORDER BY bet_id",
            (round_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [_row_to_bet(row) for row in rows]

    async def finish_round(self, result: str, dice: tuple[int, int, int]) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            """
            UPDATE sicbo_state
            SET status = ?, result = ?, dice_1 = ?, dice_2 = ?, dice_3 = ?, updated_at = ?
            WHERE id = 1
            """,
            (STATUS_RESOLVED, result, dice[0], dice[1], dice[2], now),
        )

    async def start_next_round(self, started_at: int, ends_at: int) -> SicboState:
        now = int(time.time())
        await self.db.get_connection().execute(
            """
            UPDATE sicbo_state
            SET round_id = round_id + 1,
                status = ?,
                started_at = ?,
                ends_at = ?,
                message_id = NULL,
                result = NULL,
                dice_1 = NULL,
                dice_2 = NULL,
                dice_3 = NULL,
                updated_at = ?
            WHERE id = 1
            """,
            (STATUS_BETTING, started_at, ends_at, now),
        )
        state = await self.get_state()
        if state is None:
            raise RuntimeError("Failed to start next Sicbo round")
        return state

    async def delete_old_bets(self, round_id: int) -> None:
        await self.db.get_connection().execute("DELETE FROM sicbo_bets WHERE round_id < ?", (round_id,))
