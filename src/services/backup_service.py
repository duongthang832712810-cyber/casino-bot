from __future__ import annotations

import asyncio
import logging
import sqlite3
import time
from contextlib import suppress
from pathlib import Path

import discord

from src.db.connection import Database
from src.db.transaction import immediate_transaction
from src.repositories.backup_repository import BackupRepository, BackupSettings

LOGGER = logging.getLogger(__name__)
MIN_BACKUP_INTERVAL_SECONDS = 300


class BackupService:
    def __init__(self, db: Database, repository: BackupRepository, client: discord.Client) -> None:
        self.db = db
        self.repository = repository
        self.client = client
        self._task: asyncio.Task[None] | None = None
        self._send_lock = asyncio.Lock()

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._scheduler())

    async def close(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def configure(self, channel: discord.abc.Messageable, channel_id: int, interval_minutes: int) -> BackupSettings:
        interval_seconds = max(MIN_BACKUP_INTERVAL_SECONDS, interval_minutes * 60)
        async with immediate_transaction(self.db):
            settings = await self.repository.upsert_settings(str(channel_id), interval_seconds)
        await self.send_backup_now(channel=channel, settings=settings)
        return settings

    async def disable(self) -> None:
        async with immediate_transaction(self.db):
            await self.repository.disable()

    async def send_backup_now(
        self,
        *,
        channel: discord.abc.Messageable | None = None,
        settings: BackupSettings | None = None,
    ) -> discord.Message | None:
        async with self._send_lock:
            settings = settings or await self.repository.get_settings()
            if settings is None or not settings.enabled or settings.channel_id is None:
                return None

            resolved_channel = channel or await self._resolve_channel(settings.channel_id)
            if resolved_channel is None:
                LOGGER.warning("Backup channel could not be resolved: %s", settings.channel_id)
                return None

            await self._delete_previous_backup(settings)
            backup_path = await self._create_sqlite_backup_file()
            backed_up_at = int(time.time())
            try:
                file = discord.File(str(backup_path), filename=backup_path.name)
                message = await resolved_channel.send(
                    content=f"SQLite backup created at <t:{backed_up_at}:F>.",
                    file=file,
                )
                async with immediate_transaction(self.db):
                    await self.repository.update_message(str(message.id), backed_up_at)
                return message
            finally:
                with suppress(FileNotFoundError):
                    backup_path.unlink()

    async def _scheduler(self) -> None:
        await self.client.wait_until_ready()
        while not self.client.is_closed():
            try:
                settings = await self.repository.get_settings()
                if settings is None or not settings.enabled:
                    await asyncio.sleep(60)
                    continue

                now = int(time.time())
                next_backup_at = settings.last_backup_at + settings.interval_seconds
                if settings.last_backup_at <= 0 or now >= next_backup_at:
                    await self.send_backup_now(settings=settings)
                    await asyncio.sleep(5)
                    continue

                await asyncio.sleep(min(60, max(1, next_backup_at - now)))
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.exception("Backup scheduler failed")
                await asyncio.sleep(60)

    async def _resolve_channel(self, channel_id: str) -> discord.abc.Messageable | None:
        try:
            channel = self.client.get_channel(int(channel_id)) or await self.client.fetch_channel(int(channel_id))
        except Exception:
            LOGGER.exception("Failed to resolve backup channel_id=%s", channel_id)
            return None
        return channel if isinstance(channel, discord.abc.Messageable) else None

    async def _delete_previous_backup(self, settings: BackupSettings) -> None:
        if not settings.channel_id or not settings.message_id:
            return
        try:
            channel = await self._resolve_channel(settings.channel_id)
            if channel is None or not hasattr(channel, "fetch_message"):
                return
            message = await channel.fetch_message(int(settings.message_id))  # type: ignore[attr-defined]
            await message.delete()
        except Exception as exc:
            LOGGER.warning("Failed to delete previous backup message: %s", exc)

    async def _create_sqlite_backup_file(self) -> Path:
        backup_dir = Path("data/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"casino-backup-{int(time.time())}.sqlite3"

        source = self.db.get_connection()
        with sqlite3.connect(backup_path) as target:
            await source.backup(target)
        return backup_path
