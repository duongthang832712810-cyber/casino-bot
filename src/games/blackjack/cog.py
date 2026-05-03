from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from src.core.errors import ActiveGameExistsError, InvalidBetAmountError, NotEnoughCoinsError
from src.games.blackjack.renderer import content_for_player, render_from_action
from src.games.blackjack.views import BlackjackView


class BlackjackCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="bj", description="Play Blackjack with a coin bet.")
    @app_commands.describe(amount="Coin amount to bet")
    async def slash_bj(self, interaction: discord.Interaction, amount: int) -> None:
        await self._handle_slash_bj(interaction, amount)

    @commands.command(name="bj")
    async def prefix_bj(self, ctx: commands.Context, amount: int) -> None:
        await self._handle_prefix_bj(ctx, amount)

    async def _handle_slash_bj(self, interaction: discord.Interaction, amount: int) -> None:
        service = self.bot.blackjack_service  # type: ignore[attr-defined]
        user_id = str(interaction.user.id)
        try:
            action = await service.start_or_resume(user_id, amount)
        except (ActiveGameExistsError, InvalidBetAmountError, NotEnoughCoinsError) as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        embed = render_from_action(action, interaction.user)
        content = content_for_player(user_id, action.finished)
        view = discord.ui.View() if action.finished else BlackjackView(user_id)
        await interaction.response.send_message(content=content, embed=embed, view=view)

        if not action.finished:
            message = await interaction.original_response()
            await service.save_message(user_id, message.channel.id if message.channel else None, message.id)

    async def _handle_prefix_bj(self, ctx: commands.Context, amount: int) -> None:
        service = self.bot.blackjack_service  # type: ignore[attr-defined]
        user_id = str(ctx.author.id)
        try:
            action = await service.start_or_resume(user_id, amount)
        except (ActiveGameExistsError, InvalidBetAmountError, NotEnoughCoinsError) as exc:
            await ctx.reply(str(exc), mention_author=False)
            return

        embed = render_from_action(action, ctx.author)
        content = content_for_player(user_id, action.finished)
        view = discord.ui.View() if action.finished else BlackjackView(user_id)
        message = await ctx.reply(content=content, embed=embed, view=view, mention_author=False)

        if not action.finished:
            await service.save_message(user_id, message.channel.id if message.channel else None, message.id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BlackjackCog(bot))
