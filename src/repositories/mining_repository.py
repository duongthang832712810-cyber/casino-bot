from __future__ import annotations

from aiosqlite import Row

from src.db.connection import Database
from src.games.mining.models import MiningComputer, MiningStats
from src.utils.time import utc_timestamp


def _row_to_computer(row: Row) -> MiningComputer:
    return MiningComputer(
        computer_id=row["computer_id"],
        user_id=row["user_id"],
        tier=row["tier"],
        purchase_price=row["purchase_price"],
        purchased_at=row["purchased_at"],
        last_claimed_at=row["last_claimed_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_stats(row: Row) -> MiningStats:
    return MiningStats(
        user_id=row["user_id"],
        total_claimed=row["total_claimed"],
        computers_bought=row["computers_bought"],
        highest_tier=row["highest_tier"],
        last_claimed_at=row["last_claimed_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class MiningRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_computers(self, user_id: str) -> list[MiningComputer]:
        async with self.db.get_connection().execute(
            "SELECT * FROM mining_computers WHERE user_id = ? ORDER BY tier DESC, computer_id ASC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [_row_to_computer(row) for row in rows]

    async def count_computers(self, user_id: str) -> int:
        async with self.db.get_connection().execute(
            "SELECT COUNT(*) AS count FROM mining_computers WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return int(row["count"] if row else 0)

    async def count_computers_by_tier(self, user_id: str, tier: int) -> int:
        async with self.db.get_connection().execute(
            "SELECT COUNT(*) AS count FROM mining_computers WHERE user_id = ? AND tier = ?",
            (user_id, tier),
        ) as cursor:
            row = await cursor.fetchone()
        return int(row["count"] if row else 0)

    async def count_by_tier(self, user_id: str) -> dict[int, int]:
        async with self.db.get_connection().execute(
            "SELECT tier, COUNT(*) AS count FROM mining_computers WHERE user_id = ? GROUP BY tier",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
        return {int(row["tier"]): int(row["count"]) for row in rows}

    async def create_computer(self, user_id: str, tier: int, purchase_price: int, now: int) -> MiningComputer:
        cursor = await self.db.get_connection().execute(
            """
            INSERT INTO mining_computers (user_id, tier, purchase_price, purchased_at, last_claimed_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, tier, purchase_price, now, now, now, now),
        )
        computer_id = cursor.lastrowid
        async with self.db.get_connection().execute(
            "SELECT * FROM mining_computers WHERE computer_id = ?",
            (computer_id,),
        ) as read_cursor:
            row = await read_cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to create mining computer")
        return _row_to_computer(row)

    async def update_all_claimed(self, user_id: str, now: int) -> None:
        await self.db.get_connection().execute(
            "UPDATE mining_computers SET last_claimed_at = ?, updated_at = ? WHERE user_id = ?",
            (now, now, user_id),
        )

    async def get_stats(self, user_id: str) -> MiningStats | None:
        async with self.db.get_connection().execute(
            "SELECT * FROM mining_stats WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return _row_to_stats(row) if row else None

    async def ensure_stats(self, user_id: str) -> MiningStats:
        existing = await self.get_stats(user_id)
        if existing is not None:
            return existing
        now = utc_timestamp()
        await self.db.get_connection().execute(
            """
            INSERT INTO mining_stats (user_id, total_claimed, computers_bought, highest_tier, last_claimed_at, created_at, updated_at)
            VALUES (?, 0, 0, 0, 0, ?, ?)
            ON CONFLICT(user_id) DO NOTHING
            """,
            (user_id, now, now),
        )
        stats = await self.get_stats(user_id)
        if stats is None:
            raise RuntimeError("Failed to create mining stats")
        return stats

    async def record_purchase(self, user_id: str, tier: int, now: int) -> None:
        await self.ensure_stats(user_id)
        await self.db.get_connection().execute(
            """
            UPDATE mining_stats
            SET computers_bought = computers_bought + 1,
                highest_tier = MAX(highest_tier, ?),
                updated_at = ?
            WHERE user_id = ?
            """,
            (tier, now, user_id),
        )

    async def record_claim(self, user_id: str, amount: int, now: int) -> None:
        await self.ensure_stats(user_id)
        await self.db.get_connection().execute(
            """
            UPDATE mining_stats
            SET total_claimed = total_claimed + ?,
                last_claimed_at = ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (amount, now, now, user_id),
        )
