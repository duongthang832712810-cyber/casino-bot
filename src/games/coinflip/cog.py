from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from src.config.emojis import COINFLIP_FLIP_EMOJI
from src.core.errors import ActiveGameExistsError, InvalidBetAmountError, NotEnoughCoinsError
from src.games.coinflip.renderer import render_from_action


class CoinFlipCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="cf", description="Flip a coin with a bet.")
    @app_commands.describe(choice="h/heads or t/tails", amount="Coin amount to bet")
    async def slash_coinflip(self, interaction: discord.Interaction, choice: str, amount: int) -> None:
        await self._handle_slash_coinflip(interaction, choice, amount)

    @commands.command(name="cf")
    async def prefix_coinflip(self, ctx: commands.Context, choice: str, amount: int) -> None:
        await self._handle_prefix_coinflip(ctx, choice, amount)

    async def _handle_slash_coinflip(self, interaction: discord.Interaction, choice: str, amount: int) -> None:
        service = self.bot.coinflip_service  # type: ignore[attr-defined]
        user_id = str(interaction.user.id)
        try:
            action = await service.start_or_resume(user_id, choice, amount)
        except (InvalidBetAmountError, NotEnoughCoinsError, ActiveGameExistsError) as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        if not action.is_new:
            await interaction.response.send_message("You already have a pending Coin Flip.", ephemeral=True)
            service.schedule_resolve(user_id)
            return

        embed = render_from_action(action, interaction.user)
        await interaction.response.send_message(content=COINFLIP_FLIP_EMOJI, embed=embed)
        message = await interaction.original_response()
        await service.save_message(user_id, message.channel.id if message.channel else None, message.id)
        service.schedule_resolve(user_id)

    async def _handle_prefix_coinflip(self, ctx: commands.Context, choice: str, amount: int) -> None:
        service = self.bot.coinflip_service  # type: ignore[attr-defined]
        user_id = str(ctx.author.id)
        try:
            action = await service.start_or_resume(user_id, choice, amount)
        except (InvalidBetAmountError, NotEnoughCoinsError, ActiveGameExistsError) as exc:
            await ctx.reply(str(exc), mention_author=False)
            return

        if not action.is_new:
            await ctx.reply("You already have a pending Coin Flip.", mention_author=False)
            service.schedule_resolve(user_id)
            return

        embed = render_from_action(action, ctx.author)
        message = await ctx.reply(content=COINFLIP_FLIP_EMOJI, embed=embed, mention_author=False)
        await service.save_message(user_id, message.channel.id if message.channel else None, message.id)
        service.schedule_resolve(user_id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CoinFlipCog(bot))
