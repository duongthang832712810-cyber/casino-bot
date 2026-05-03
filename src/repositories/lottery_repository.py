from __future__ import annotations

import time

from aiosqlite import Row

from src.db.connection import Database
from src.games.lottery.models import LotteryAnnouncement, LotteryState, LotteryTicket


def _row_to_state(row: Row) -> LotteryState:
    return LotteryState(
        draw_id=row["draw_id"],
        status=row["status"],
        jackpot_pool=row["jackpot_pool"],
        started_at=row["started_at"],
        ends_at=row["ends_at"],
        tickets_sold=row["tickets_sold"],
        participants=row["participants"],
        announcement_channel_id=row["announcement_channel_id"],
        announcement_message_id=row["announcement_message_id"],
        last_draw_number=row["last_draw_number"],
        last_jackpot_winners=row["last_jackpot_winners"],
        last_total_payout=row["last_total_payout"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_announcement(row: Row) -> LotteryAnnouncement:
    return LotteryAnnouncement(
        guild_id=row["guild_id"],
        channel_id=row["channel_id"],
        message_id=row["message_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_ticket(row: Row) -> LotteryTicket:
    return LotteryTicket(
        ticket_id=row["ticket_id"],
        draw_id=row["draw_id"],
        user_id=row["user_id"],
        number=row["number"],
        quantity=row["quantity"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class LotteryRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_state(self) -> LotteryState | None:
        async with self.db.get_connection().execute("SELECT * FROM lottery_state WHERE id = 1") as cursor:
            row = await cursor.fetchone()
        return _row_to_state(row) if row else None

    async def create_state(self, jackpot_pool: int, started_at: int, ends_at: int) -> LotteryState:
        now = int(time.time())
        await self.db.get_connection().execute(
            """
            INSERT INTO lottery_state (
                id, draw_id, status, jackpot_pool, started_at, ends_at,
                tickets_sold, participants, created_at, updated_at
            ) VALUES (1, 1, 'open', ?, ?, ?, 0, 0, ?, ?)
            """,
            (jackpot_pool, started_at, ends_at, now, now),
        )
        state = await self.get_state()
        if state is None:
            raise RuntimeError("Failed to create lottery state")
        return state

    async def update_announcement(self, channel_id: str | None, message_id: str | None) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            "UPDATE lottery_state SET announcement_channel_id = ?, announcement_message_id = ?, updated_at = ? WHERE id = 1",
            (channel_id, message_id, now),
        )

    async def get_announcement(self, guild_id: str) -> LotteryAnnouncement | None:
        async with self.db.get_connection().execute(
            "SELECT * FROM lottery_announcements WHERE guild_id = ?",
            (guild_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return _row_to_announcement(row) if row else None

    async def list_announcements(self) -> list[LotteryAnnouncement]:
        async with self.db.get_connection().execute(
            "SELECT * FROM lottery_announcements ORDER BY guild_id"
        ) as cursor:
            rows = await cursor.fetchall()
        return [_row_to_announcement(row) for row in rows]

    async def upsert_announcement(self, guild_id: str, channel_id: str, message_id: str | None) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            """
            INSERT INTO lottery_announcements (guild_id, channel_id, message_id, created_at, updated_at)
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
            "UPDATE lottery_announcements SET message_id = ?, updated_at = ? WHERE guild_id = ?",
            (message_id, now, guild_id),
        )

    async def set_status(self, status: str) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            "UPDATE lottery_state SET status = ?, updated_at = ? WHERE id = 1",
            (status, now),
        )

    async def add_purchase(self, draw_id: int, user_id: str, numbers: dict[str, int], jackpot_add: int, is_new_participant: bool) -> None:
        now = int(time.time())
        conn = self.db.get_connection()
        for number, quantity in numbers.items():
            await conn.execute(
                """
                INSERT INTO lottery_tickets (draw_id, user_id, number, quantity, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(draw_id, user_id, number) DO UPDATE SET
                    quantity = quantity + excluded.quantity,
                    updated_at = excluded.updated_at
                """,
                (draw_id, user_id, number, quantity, now, now),
            )

        participants_inc = 1 if is_new_participant else 0
        tickets_sold_inc = sum(numbers.values())
        await conn.execute(
            """
            UPDATE lottery_state
            SET jackpot_pool = jackpot_pool + ?,
                tickets_sold = tickets_sold + ?,
                participants = participants + ?,
                updated_at = ?
            WHERE id = 1
            """,
            (jackpot_add, tickets_sold_inc, participants_inc, now),
        )

    async def user_has_ticket(self, draw_id: int, user_id: str) -> bool:
        async with self.db.get_connection().execute(
            "SELECT 1 FROM lottery_tickets WHERE draw_id = ? AND user_id = ? LIMIT 1",
            (draw_id, user_id),
        ) as cursor:
            return await cursor.fetchone() is not None

    async def user_ticket_quantity(self, draw_id: int, user_id: str) -> int:
        async with self.db.get_connection().execute(
            "SELECT COALESCE(SUM(quantity), 0) AS total FROM lottery_tickets WHERE draw_id = ? AND user_id = ?",
            (draw_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
        return int(row["total"] if row else 0)

    async def list_tickets(self, draw_id: int) -> list[LotteryTicket]:
        async with self.db.get_connection().execute(
            "SELECT * FROM lottery_tickets WHERE draw_id = ? ORDER BY ticket_id",
            (draw_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [_row_to_ticket(row) for row in rows]

    async def list_user_tickets(self, draw_id: int, user_id: str) -> list[LotteryTicket]:
        async with self.db.get_connection().execute(
            "SELECT * FROM lottery_tickets WHERE draw_id = ? AND user_id = ? ORDER BY number",
            (draw_id, user_id),
        ) as cursor:
            rows = await cursor.fetchall()
        return [_row_to_ticket(row) for row in rows]

    async def reset_for_next_draw(
        self,
        old_draw_id: int,
        new_jackpot_pool: int,
        winning_number: str,
        jackpot_winners: int,
        total_payout: int,
        started_at: int,
        ends_at: int,
    ) -> None:
        now = int(time.time())
        conn = self.db.get_connection()
        await conn.execute("DELETE FROM lottery_tickets WHERE draw_id = ?", (old_draw_id,))
        await conn.execute(
            """
            UPDATE lottery_state
            SET draw_id = draw_id + 1,
                status = 'open',
                jackpot_pool = ?,
                started_at = ?,
                ends_at = ?,
                tickets_sold = 0,
                participants = 0,
                last_draw_number = ?,
                last_jackpot_winners = ?,
                last_total_payout = ?,
                updated_at = ?
            WHERE id = 1
            """,
            (new_jackpot_pool, started_at, ends_at, winning_number, jackpot_winners, total_payout, now),
        )
