from __future__ import annotations

import time
from dataclasses import dataclass

from aiosqlite import Row

from src.db.connection import Database


@dataclass(frozen=True, slots=True)
class BackupSettings:
    channel_id: str | None
    message_id: str | None
    interval_seconds: int
    enabled: bool
    last_backup_at: int
    created_at: int
    updated_at: int


def _row_to_settings(row: Row) -> BackupSettings:
    return BackupSettings(
        channel_id=row["channel_id"],
        message_id=row["message_id"],
        interval_seconds=row["interval_seconds"],
        enabled=bool(row["enabled"]),
        last_backup_at=row["last_backup_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class BackupRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_settings(self) -> BackupSettings | None:
        async with self.db.get_connection().execute("SELECT * FROM backup_settings WHERE id = 1") as cursor:
            row = await cursor.fetchone()
        return _row_to_settings(row) if row else None

    async def upsert_settings(self, channel_id: str, interval_seconds: int) -> BackupSettings:
        now = int(time.time())
        await self.db.get_connection().execute(
            """
            INSERT INTO backup_settings (
                id, channel_id, message_id, interval_seconds, enabled,
                last_backup_at, created_at, updated_at
            ) VALUES (1, ?, NULL, ?, 1, 0, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                channel_id = excluded.channel_id,
                interval_seconds = excluded.interval_seconds,
                enabled = 1,
                updated_at = excluded.updated_at
            """,
            (channel_id, interval_seconds, now, now),
        )
        settings = await self.get_settings()
        if settings is None:
            raise RuntimeError("Failed to save backup settings")
        return settings

    async def update_message(self, message_id: str, backed_up_at: int) -> None:
        await self.db.get_connection().execute(
            """
            UPDATE backup_settings
            SET message_id = ?, last_backup_at = ?, updated_at = ?
            WHERE id = 1
            """,
            (message_id, backed_up_at, backed_up_at),
        )

    async def disable(self) -> None:
        now = int(time.time())
        await self.db.get_connection().execute(
            "UPDATE backup_settings SET enabled = 0, updated_at = ? WHERE id = 1",
            (now,),
        )
