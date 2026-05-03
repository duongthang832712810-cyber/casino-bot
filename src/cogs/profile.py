from __future__ import annotations

import random

import discord
from discord import app_commands
from discord.ext import commands

from src.config.emojis import COIN_ICON_URL, EXP_EMOJI, TICKET_EMOJI
from src.utils.money import format_coin, format_number


PROFILE_FOOTER_MESSAGES = (
    "Keep stacking your coins.",
    "Every hand tells a story.",
    "Your casino journey continues.",
    "Play smart, build your fortune.",
)


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="profile", description="View your casino profile.")
    async def slash_profile(self, interaction: discord.Interaction) -> None:
        await self._send_profile(interaction, str(interaction.user.id), interaction.user)

    @commands.command(name="profile")
    async def prefix_profile(self, ctx: commands.Context) -> None:
        user_id = str(ctx.author.id)
        user = await self.bot.user_repository.get_or_create(user_id, self.bot.settings.default_coins)  # type: ignore[attr-defined,union-attr]
        tickets_count = await self._current_lottery_ticket_count(user_id)
        await ctx.reply(embed=self._build_embed(ctx.author, user, tickets_count), mention_author=False)

    async def _send_profile(self, interaction: discord.Interaction, user_id: str, member: discord.abc.User) -> None:
        user = await self.bot.user_repository.get_or_create(user_id, self.bot.settings.default_coins)  # type: ignore[attr-defined,union-attr]
        tickets_count = await self._current_lottery_ticket_count(user_id)
        await interaction.response.send_message(embed=self._build_embed(member, user, tickets_count), ephemeral=True)

    async def _current_lottery_ticket_count(self, user_id: str) -> int:
        service = getattr(self.bot, "lottery_service", None)
        if service is None:
            return 0
        _state, tickets = await service.get_user_tickets(user_id)
        return sum(ticket.quantity for ticket in tickets)

    @staticmethod
    def _build_embed(member: discord.abc.User, user, tickets_count: int) -> discord.Embed:
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name=f"{member.display_name}'s Profile", icon_url=member.display_avatar.url)
        embed.add_field(
            name="Stats",
            value=(
                f"Win: {format_number(user.wins)}\n"
                f"Lose: {format_number(user.losses)}\n"
                f"Draw: {format_number(user.draws)}"
            ),
            inline=True,
        )
        embed.add_field(
            name="Coins",
            value=(
                f"{format_coin(user.coins)}\n"
                f"**Exp**\n{format_number(user.exp)} {EXP_EMOJI}\n"
                f"**Ticket**\n{format_number(tickets_count)} {TICKET_EMOJI}"
            ),
            inline=True,
        )
        footer = ProfileCog._footer_message()
        embed.set_footer(text=footer, icon_url=COIN_ICON_URL)
        return embed

    @staticmethod
    def _footer_message() -> str:
        return random.choice(PROFILE_FOOTER_MESSAGES)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ProfileCog(bot))
