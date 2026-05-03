from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from src.db.connection import Database


@asynccontextmanager
async def immediate_transaction(db: Database) -> AsyncIterator[None]:
    conn = db.get_connection()
    async with db.write_lock:
        await conn.execute("BEGIN IMMEDIATE")
        try:
            yield
        except Exception:
            await conn.rollback()
            raise
        else:
            await conn.commit()
