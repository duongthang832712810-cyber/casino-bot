from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from src.services.backup_service import MIN_BACKUP_INTERVAL_SECONDS
from src.utils.time import format_duration


class BackupCog(commands.Cog):
    backup = app_commands.Group(name="backup", description="Owner-only SQLite backup commands.")

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @backup.command(name="set", description="Set the backup channel and interval.")
    @app_commands.describe(channel="Channel that receives SQLite backup files", interval_minutes="Backup interval in minutes")
    async def slash_set(self, interaction: discord.Interaction, channel: discord.TextChannel, interval_minutes: int) -> None:
        if not await self._check_owner(interaction):
            return
        if interval_minutes * 60 < MIN_BACKUP_INTERVAL_SECONDS:
            await interaction.response.send_message(
                f"Backup interval must be at least {format_duration(MIN_BACKUP_INTERVAL_SECONDS)}.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        service = self.bot.backup_service  # type: ignore[attr-defined]
        settings = await service.configure(channel, channel.id, interval_minutes)
        await interaction.followup.send(
            f"Backup enabled in {channel.mention}. Interval: {format_duration(settings.interval_seconds)}.",
            ephemeral=True,
        )

    @backup.command(name="now", description="Send a SQLite backup now.")
    async def slash_now(self, interaction: discord.Interaction) -> None:
        if not await self._check_owner(interaction):
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        service = self.bot.backup_service  # type: ignore[attr-defined]
        message = await service.send_backup_now()
        if message is None:
            await interaction.followup.send("Backup is not configured. Use `/backup set` first.", ephemeral=True)
            return
        await interaction.followup.send("Backup sent.", ephemeral=True)

    @backup.command(name="off", description="Disable automatic SQLite backups.")
    async def slash_off(self, interaction: discord.Interaction) -> None:
        if not await self._check_owner(interaction):
            return
        service = self.bot.backup_service  # type: ignore[attr-defined]
        await service.disable()
        await interaction.response.send_message("Automatic backups disabled.", ephemeral=True)

    @backup.command(name="status", description="View SQLite backup settings.")
    async def slash_status(self, interaction: discord.Interaction) -> None:
        if not await self._check_owner(interaction):
            return
        repository = self.bot.backup_repository  # type: ignore[attr-defined]
        settings = await repository.get_settings()
        if settings is None:
            await interaction.response.send_message("Backup is not configured.", ephemeral=True)
            return

        channel_text = f"<#{settings.channel_id}>" if settings.channel_id else "Not set"
        last_backup = f"<t:{settings.last_backup_at}:R>" if settings.last_backup_at > 0 else "Never"
        status = "Enabled" if settings.enabled else "Disabled"
        await interaction.response.send_message(
            "\n".join(
                (
                    f"Status: **{status}**",
                    f"Channel: {channel_text}",
                    f"Interval: **{format_duration(settings.interval_seconds)}**",
                    f"Last backup: {last_backup}",
                )
            ),
            ephemeral=True,
        )

    async def _check_owner(self, interaction: discord.Interaction) -> bool:
        owner_id = getattr(self.bot.settings, "owner_id", None)  # type: ignore[attr-defined]
        if owner_id is None:
            await interaction.response.send_message("Bot owner is not configured.", ephemeral=True)
            return False
        if interaction.user.id != owner_id:
            await interaction.response.send_message("Only the bot owner can use this command.", ephemeral=True)
            return False
        return True


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BackupCog(bot))
