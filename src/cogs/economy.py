from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from src.core.errors import DailyRewardCooldownError, InvalidBetAmountError, NotEnoughCoinsError
from src.db.transaction import immediate_transaction
from src.utils.money import format_coin, format_number


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="balance", description="View your coin balance.")
    async def slash_balance(self, interaction: discord.Interaction) -> None:
        await self._send_slash_balance(interaction)

    @app_commands.command(name="bal", description="View your coin balance.")
    async def slash_bal(self, interaction: discord.Interaction) -> None:
        await self._send_slash_balance(interaction)

    @app_commands.command(name="daily", description="Claim your daily coin reward.")
    async def slash_daily(self, interaction: discord.Interaction) -> None:
        try:
            message = await self._claim_daily(str(interaction.user.id))
        except DailyRewardCooldownError as exc:
            message = f"You can claim your daily reward again in {_format_duration(exc.retry_after_seconds)}."
        await interaction.response.send_message(message, ephemeral=True)

    @app_commands.command(name="give", description="Give coins to another user.")
    @app_commands.describe(user="User to receive coins", amount="Coin amount to give")
    async def slash_give(self, interaction: discord.Interaction, user: discord.User, amount: int) -> None:
        try:
            message = await self._give_coins(str(interaction.user.id), str(user.id), amount)
        except (InvalidBetAmountError, NotEnoughCoinsError) as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await interaction.response.send_message(message)

    @commands.command(name="balance", aliases=["bal"])
    async def prefix_balance(self, ctx: commands.Context) -> None:
        user = await self.bot.user_repository.get_or_create(str(ctx.author.id), self.bot.settings.default_coins)  # type: ignore[attr-defined,union-attr]
        await ctx.reply(f"Your balance is {format_coin(user.coins)}.", mention_author=True)

    @commands.command(name="daily")
    async def prefix_daily(self, ctx: commands.Context) -> None:
        try:
            message = await self._claim_daily(str(ctx.author.id))
        except DailyRewardCooldownError as exc:
            message = f"You can claim your daily reward again in {_format_duration(exc.retry_after_seconds)}."
        await ctx.reply(message, mention_author=True)

    @commands.command(name="give")
    async def prefix_give(self, ctx: commands.Context, user: discord.User, amount: int) -> None:
        try:
            message = await self._give_coins(str(ctx.author.id), str(user.id), amount)
        except (InvalidBetAmountError, NotEnoughCoinsError) as exc:
            await ctx.reply(str(exc), mention_author=True)
            return
        await ctx.reply(message, mention_author=True)

    async def _send_slash_balance(self, interaction: discord.Interaction) -> None:
        user = await self.bot.user_repository.get_or_create(str(interaction.user.id), self.bot.settings.default_coins)  # type: ignore[attr-defined,union-attr]
        await interaction.response.send_message(f"Your balance is {format_coin(user.coins)}.", ephemeral=True)

    async def _claim_daily(self, user_id: str) -> str:
        claim = await self.bot.daily_reward_service.claim(user_id)  # type: ignore[attr-defined,union-attr]
        return f"Daily reward claimed! You received {format_coin(claim.reward)}. New balance: {format_coin(claim.new_balance)}."

    async def _give_coins(self, sender_id: str, recipient_id: str, amount: int) -> str:
        if sender_id == recipient_id:
            raise InvalidBetAmountError("You cannot give coins to yourself.")
        if amount <= 0:
            raise InvalidBetAmountError("Amount must be greater than 0.")

        users = self.bot.user_repository  # type: ignore[attr-defined,union-attr]
        await users.get_or_create(sender_id, self.bot.settings.default_coins)  # type: ignore[attr-defined,union-attr]
        await users.get_or_create(recipient_id, self.bot.settings.default_coins)  # type: ignore[attr-defined,union-attr]

        async with immediate_transaction(self.bot.db):  # type: ignore[attr-defined]
            sender = await users.get_by_id(sender_id)
            if sender is None:
                raise RuntimeError("Sender disappeared")
            if sender.coins < amount:
                raise NotEnoughCoinsError("Not enough coins to give.")
            await users.add_coins(sender_id, -amount)
            await users.add_coins(recipient_id, amount)

        return f"Gave {format_coin(amount)} to <@{recipient_id}>."


def _format_duration(seconds: int) -> str:
    seconds = max(0, seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, remaining_seconds = divmod(remainder, 60)

    parts: list[str] = []
    if hours:
        parts.append(f"{format_number(hours)}h")
    if minutes:
        parts.append(f"{format_number(minutes)}m")
    if remaining_seconds or not parts:
        parts.append(f"{format_number(remaining_seconds)}s")
    return " ".join(parts)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EconomyCog(bot))
