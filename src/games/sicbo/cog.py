from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from src.core.errors import ActiveGameExistsError, InvalidBetAmountError, NotEnoughCoinsError
from src.games.sicbo.constants import CHOICE_DISPLAY
from src.games.sicbo.renderer import render_sicbo_embed
from src.games.sicbo.service import SicboBettingClosedError, SicboChannelNotSetError
from src.utils.money import format_coin

LOGGER = logging.getLogger(__name__)


class SicboCog(commands.Cog):
    sicbo = app_commands.Group(name="sb", description="Sicbo commands.")

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @sicbo.command(name="bet", description="Place a bet.")
    @app_commands.describe(choice="big/tai or small/xiu", amount="Coin bet amount")
    async def slash_bet(self, interaction: discord.Interaction, choice: str, amount: int) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        service = self.bot.sicbo_service  # type: ignore[attr-defined]
        try:
            result = await service.place_bet(interaction.guild_id, str(interaction.user.id), choice, amount)
        except (ActiveGameExistsError, InvalidBetAmountError, NotEnoughCoinsError, SicboBettingClosedError, SicboChannelNotSetError) as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await interaction.response.send_message(_bet_message(result.user_bet.choice, result.user_bet.amount), ephemeral=True)

    @sicbo.command(name="info", description="View current round information.")
    async def slash_info(self, interaction: discord.Interaction) -> None:
        service = self.bot.sicbo_service  # type: ignore[attr-defined]
        view = await service.get_round_view()
        await interaction.response.send_message(embed=render_sicbo_embed(view.state, view.bets), ephemeral=True)

    @sicbo.command(name="set", description="Set the announcement channel.")
    @app_commands.describe(channel="Announcement channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        service = self.bot.sicbo_service  # type: ignore[attr-defined]
        await service.set_channel(interaction.guild_id, channel, channel.id)
        await interaction.response.send_message(f"Sicbo channel set to {channel.mention}.", ephemeral=True)

    @commands.group(name="sb")
    async def prefix_sicbo(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.reply(f"Usage: `{ctx.clean_prefix}sb <bet|info|set>`", mention_author=True)

    @prefix_sicbo.command(name="bet")
    async def prefix_bet(self, ctx: commands.Context, choice: str, amount: int) -> None:
        await self._handle_prefix_bet(ctx, choice, amount)

    @prefix_sicbo.command(name="info")
    async def prefix_info(self, ctx: commands.Context) -> None:
        await self._send_prefix_info(ctx)

    @prefix_sicbo.command(name="set")
    @commands.has_guild_permissions(administrator=True)
    async def prefix_set(self, ctx: commands.Context, channel: discord.TextChannel) -> None:
        if ctx.guild is None:
            await ctx.reply("This command can only be used in a server.", mention_author=True)
            return
        service = self.bot.sicbo_service  # type: ignore[attr-defined]
        await service.set_channel(ctx.guild.id, channel, channel.id)
        await ctx.reply(f"Sicbo channel set to {channel.mention}.", mention_author=True)

    async def _handle_prefix_bet(self, ctx: commands.Context, choice: str, amount: int) -> None:
        if ctx.guild is None:
            await ctx.reply("This command can only be used in a server.", mention_author=True)
            return
        service = self.bot.sicbo_service  # type: ignore[attr-defined]
        try:
            result = await service.place_bet(ctx.guild.id, str(ctx.author.id), choice, amount)
        except (ActiveGameExistsError, InvalidBetAmountError, NotEnoughCoinsError, SicboBettingClosedError, SicboChannelNotSetError) as exc:
            await ctx.reply(str(exc), mention_author=True)
            return
        await ctx.reply(_bet_message(result.user_bet.choice, result.user_bet.amount), mention_author=True)

    async def _send_prefix_info(self, ctx: commands.Context) -> None:
        service = self.bot.sicbo_service  # type: ignore[attr-defined]
        view = await service.get_round_view()
        await ctx.reply(embed=render_sicbo_embed(view.state, view.bets), mention_author=True)


def _bet_message(choice: str, amount: int) -> str:
    return f"Placed {format_coin(amount)} on {CHOICE_DISPLAY[choice]}."


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SicboCog(bot))
