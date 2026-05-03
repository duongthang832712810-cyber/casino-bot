from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from src.core.errors import ActiveGameExistsError, InvalidBetAmountError, NotEnoughCoinsError
from src.games.lottery.renderer import render_announcement_embed, render_user_tickets_embed
from src.games.lottery.service import LotteryDrawClosedError
from src.utils.money import format_coin, format_number


class LotteryCog(commands.Cog):
    lottery = app_commands.Group(name="lt", description="Lottery commands.")

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @lottery.command(name="buy", description="Buy tickets with a chosen number.")
    @app_commands.describe(number="Number from 0001 to 9999", quantity="Ticket quantity")
    async def slash_buy(self, interaction: discord.Interaction, number: str, quantity: int = 1) -> None:
        await self._handle_slash_buy(interaction, number, quantity)

    @lottery.command(name="random", description="Buy tickets with random numbers.")
    @app_commands.describe(quantity="Ticket quantity")
    async def slash_random(self, interaction: discord.Interaction, quantity: int = 1) -> None:
        await self._handle_slash_random(interaction, quantity)

    @lottery.command(name="tickets", description="View your current tickets.")
    async def slash_tickets(self, interaction: discord.Interaction) -> None:
        service = self.bot.lottery_service  # type: ignore[attr-defined]
        state, tickets = await service.get_user_tickets(str(interaction.user.id))
        await interaction.response.send_message(embed=render_user_tickets_embed(state, tickets, interaction.user), ephemeral=True)

    @lottery.command(name="info", description="View current round information.")
    async def slash_info(self, interaction: discord.Interaction) -> None:
        service = self.bot.lottery_service  # type: ignore[attr-defined]
        state = await service.get_state()
        await interaction.response.send_message(embed=render_announcement_embed(state), ephemeral=True)

    @lottery.command(name="set", description="Set the announcement channel.")
    @app_commands.describe(channel="Announcement channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        service = self.bot.lottery_service  # type: ignore[attr-defined]
        await service.set_announcement_channel(interaction.guild_id, channel, channel.id)
        await interaction.response.send_message(f"Lottery announcement channel set to {channel.mention}.", ephemeral=True)

    @commands.group(name="lt")
    async def prefix_lottery(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.reply(f"Usage: `{ctx.clean_prefix}lt <buy|random|tickets|info|set>`", mention_author=True)

    @prefix_lottery.command(name="buy")
    async def prefix_buy(self, ctx: commands.Context, number: str, quantity: int = 1) -> None:
        await self._handle_prefix_buy(ctx, number, quantity)

    @prefix_lottery.command(name="random")
    async def prefix_random(self, ctx: commands.Context, quantity: int = 1) -> None:
        await self._handle_prefix_random(ctx, quantity)

    @prefix_lottery.command(name="tickets")
    async def prefix_tickets(self, ctx: commands.Context) -> None:
        service = self.bot.lottery_service  # type: ignore[attr-defined]
        state, tickets = await service.get_user_tickets(str(ctx.author.id))
        await ctx.reply(embed=render_user_tickets_embed(state, tickets, ctx.author), mention_author=True)

    @prefix_lottery.command(name="info")
    async def prefix_info(self, ctx: commands.Context) -> None:
        service = self.bot.lottery_service  # type: ignore[attr-defined]
        state = await service.get_state()
        await ctx.reply(embed=render_announcement_embed(state), mention_author=True)

    @prefix_lottery.command(name="set")
    @commands.has_guild_permissions(administrator=True)
    async def prefix_set(self, ctx: commands.Context, channel: discord.TextChannel) -> None:
        if ctx.guild is None:
            await ctx.reply("This command can only be used in a server.", mention_author=True)
            return
        service = self.bot.lottery_service  # type: ignore[attr-defined]
        await service.set_announcement_channel(ctx.guild.id, channel, channel.id)
        await ctx.reply(f"Lottery announcement channel set to {channel.mention}.", mention_author=True)

    async def _handle_slash_buy(self, interaction: discord.Interaction, number: str, quantity: int) -> None:
        service = self.bot.lottery_service  # type: ignore[attr-defined]
        try:
            result = await service.buy(str(interaction.user.id), number, quantity)
        except (ActiveGameExistsError, InvalidBetAmountError, LotteryDrawClosedError, NotEnoughCoinsError) as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await interaction.response.send_message(_purchase_message(result), ephemeral=True)

    async def _handle_slash_random(self, interaction: discord.Interaction, quantity: int) -> None:
        service = self.bot.lottery_service  # type: ignore[attr-defined]
        try:
            result = await service.buy_random(str(interaction.user.id), quantity)
        except (ActiveGameExistsError, InvalidBetAmountError, LotteryDrawClosedError, NotEnoughCoinsError) as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await interaction.response.send_message(_purchase_message(result), ephemeral=True)

    async def _handle_prefix_buy(self, ctx: commands.Context, number: str, quantity: int) -> None:
        service = self.bot.lottery_service  # type: ignore[attr-defined]
        try:
            result = await service.buy(str(ctx.author.id), number, quantity)
        except (ActiveGameExistsError, InvalidBetAmountError, LotteryDrawClosedError, NotEnoughCoinsError) as exc:
            await ctx.reply(str(exc), mention_author=True)
            return
        await ctx.reply(_purchase_message(result), mention_author=True)

    async def _handle_prefix_random(self, ctx: commands.Context, quantity: int) -> None:
        service = self.bot.lottery_service  # type: ignore[attr-defined]
        try:
            result = await service.buy_random(str(ctx.author.id), quantity)
        except (ActiveGameExistsError, InvalidBetAmountError, LotteryDrawClosedError, NotEnoughCoinsError) as exc:
            await ctx.reply(str(exc), mention_author=True)
            return
        await ctx.reply(_purchase_message(result), mention_author=True)


def _purchase_message(result) -> str:
    number_text = ", ".join(
        f"{number} × {format_number(quantity)}" for number, quantity in sorted(result.numbers.items())
    )
    return (
        f"Bought {format_number(result.total_quantity)} Lottery ticket(s) for {format_coin(result.total_cost)}. "
        f"Numbers: {number_text}"
    )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LotteryCog(bot))
