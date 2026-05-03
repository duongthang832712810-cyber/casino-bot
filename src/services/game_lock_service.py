from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator


class GameLockService:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._guard = asyncio.Lock()

    async def _get_lock(self, user_id: str) -> asyncio.Lock:
        async with self._guard:
            if user_id not in self._locks:
                self._locks[user_id] = asyncio.Lock()
            return self._locks[user_id]

    @asynccontextmanager
    async def lock(self, user_id: str) -> AsyncIterator[None]:
        lock = await self._get_lock(user_id)
        async with lock:
            yield
