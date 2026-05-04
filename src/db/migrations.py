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

    columns: dict[str, str] = {
        "daily_claimed_at": "INTEGER NOT NULL DEFAULT 0",
        "level": "INTEGER NOT NULL DEFAULT 0 CHECK (level >= 0)",
        "total_bet": "INTEGER NOT NULL DEFAULT 0 CHECK (total_bet >= 0)",
        "total_payout": "INTEGER NOT NULL DEFAULT 0 CHECK (total_payout >= 0)",
        "net_profit": "INTEGER NOT NULL DEFAULT 0",
        "achievements_unlocked": "INTEGER NOT NULL DEFAULT 0 CHECK (achievements_unlocked >= 0)",
        "current_win_streak": "INTEGER NOT NULL DEFAULT 0 CHECK (current_win_streak >= 0)",
        "current_loss_streak": "INTEGER NOT NULL DEFAULT 0 CHECK (current_loss_streak >= 0)",
        "best_win_streak": "INTEGER NOT NULL DEFAULT 0 CHECK (best_win_streak >= 0)",
        "best_loss_streak": "INTEGER NOT NULL DEFAULT 0 CHECK (best_loss_streak >= 0)",
    }
    for column_name, definition in columns.items():
        if column_name not in column_names:
            await conn.execute(f"ALTER TABLE users ADD COLUMN {column_name} {definition}")
