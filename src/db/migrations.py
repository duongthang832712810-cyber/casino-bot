from __future__ import annotations

from pathlib import Path

from src.db.connection import Database


async def run_migrations(db: Database) -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    sql = schema_path.read_text(encoding="utf-8")
    conn = db.get_connection()
    await conn.executescript(sql)
    await _ensure_users_columns(db)
    await conn.commit()


async def _ensure_users_columns(db: Database) -> None:
    conn = db.get_connection()
    async with conn.execute("PRAGMA table_info(users)") as cursor:
        rows = await cursor.fetchall()
    column_names = {row[1] for row in rows}

    if "daily_claimed_at" not in column_names:
        await conn.execute("ALTER TABLE users ADD COLUMN daily_claimed_at INTEGER NOT NULL DEFAULT 0")
