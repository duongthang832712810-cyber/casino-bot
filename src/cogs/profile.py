from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from src.config.achievements import GAME_NAMES, GAME_TYPES
from src.config.emojis import COIN_ICON_URL, EXP_EMOJI, TICKET_EMOJI
from src.models.game_stats import GameStats
from src.services.achievement_service import AchievementService
from src.services.progression_service import ProgressionService
from src.utils.footer import random_footer_text
from src.utils.money import format_coin, format_number
from src.utils.rank import rank_for_level

PAGE_NAMES = ("Overview", "Blackjack", "Coin Flip", "Lottery", "Sicbo", "Baucua", "Achievements")


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="profile", description="View your casino profile.")
    async def slash_profile(self, interaction: discord.Interaction) -> None:
        view = await self._build_view(str(interaction.user.id), interaction.user)
        await interaction.response.send_message(embed=view.embed(), view=view, ephemeral=True)

    @commands.command(name="profile")
    async def prefix_profile(self, ctx: commands.Context) -> None:
        view = await self._build_view(str(ctx.author.id), ctx.author)
        await ctx.reply(embed=view.embed(), view=view, mention_author=True)

    async def _build_view(self, user_id: str, member: discord.abc.User) -> "ProfileView":
        user = await self.bot.user_repository.get_or_create(user_id, self.bot.settings.default_coins)  # type: ignore[attr-defined,union-attr]
        tickets_count = await self._current_lottery_ticket_count(user_id)
        stats_service = self.bot.game_stats_service  # type: ignore[attr-defined]
        stats = {item.game_type: item for item in await stats_service.list_by_user(user_id)}
        achievement_service = self.bot.achievement_service  # type: ignore[attr-defined]
        achievements = await achievement_service.list_user_achievements(user_id)
        return ProfileView(member.id, member, user, tickets_count, stats, achievements, _bot_name(self.bot))

    async def _current_lottery_ticket_count(self, user_id: str) -> int:
        service = getattr(self.bot, "lottery_service", None)
        if service is None:
            return 0
        _state, tickets = await service.get_user_tickets(user_id)
        return sum(ticket.quantity for ticket in tickets)


class ProfileView(discord.ui.View):
    def __init__(self, owner_id: int, member: discord.abc.User, user, tickets_count: int, stats: dict[str, GameStats], achievements, bot_name: str | None) -> None:
        super().__init__(timeout=180)
        self.owner_id = owner_id
        self.member = member
        self.user = user
        self.tickets_count = tickets_count
        self.stats = stats
        self.achievements = achievements
        self.bot_name = bot_name
        self.page = 0
        self._update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.owner_id:
            return True
        await interaction.response.send_message("This profile menu is not yours.", ephemeral=True)
        return False

    @discord.ui.button(style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.page = len(PAGE_NAMES) - 1 if self.page == 0 else self.page - 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.page = 0 if self.page == len(PAGE_NAMES) - 1 else self.page + 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embed(), view=self)

    def _update_buttons(self) -> None:
        self.previous_page.label = f"Previous: {PAGE_NAMES[len(PAGE_NAMES) - 1 if self.page == 0 else self.page - 1]}"
        self.next_page.label = f"Next: {PAGE_NAMES[0 if self.page == len(PAGE_NAMES) - 1 else self.page + 1]}"

    def embed(self) -> discord.Embed:
        if self.page == 0:
            return self._overview_embed()
        if self.page == len(PAGE_NAMES) - 1:
            return self._achievements_embed()
        return self._game_embed(GAME_TYPES[self.page - 1])

    def _base_embed(self, title: str) -> discord.Embed:
        embed = discord.Embed(title=title, description=self._progress_text(), color=discord.Color.green())
        embed.set_author(name=f"{self.member.display_name}'s Profile", icon_url=self.member.display_avatar.url)
        embed.set_footer(text=random_footer_text(self.bot_name), icon_url=COIN_ICON_URL)
        return embed

    def _progress_text(self) -> str:
        progress = ProgressionService.level_progress(self.user.level, self.user.exp)
        rank = rank_for_level(progress.level)
        return f"{rank.emoji} Lv.{format_number(progress.level)} {progress.bar} {format_number(progress.exp)}/{format_number(progress.required_exp)} {EXP_EMOJI}"

    def _overview_embed(self) -> discord.Embed:
        embed = self._base_embed("Profile Overview")
        embed.add_field(name="Coins", value=f"{format_coin(self.user.coins)}\n**Ticket**\n{format_number(self.tickets_count)} {TICKET_EMOJI}", inline=True)
        embed.add_field(name="Global Stats", value=_stats_text(self.user), inline=True)
        embed.add_field(
            name="Totals",
            value=(
                f"Bet: {format_coin(self.user.total_bet)}\n"
                f"Payout: {format_coin(self.user.total_payout)}\n"
                f"Profit: {format_coin(self.user.net_profit)}\n"
                f"Achievements: {format_number(self.user.achievements_unlocked)}/{format_number(AchievementService.total_count())}"
            ),
            inline=False,
        )
        return embed

    def _game_embed(self, game_type: str) -> discord.Embed:
        embed = self._base_embed(f"{GAME_NAMES[game_type]} Stats")
        stats = self.stats.get(game_type)
        if stats is None:
            embed.add_field(name="Stats", value="No games played yet.", inline=False)
            return embed
        embed.add_field(name="Results", value=_stats_text(stats), inline=True)
        embed.add_field(
            name="Streaks",
            value=(
                f"Win: {format_number(stats.current_win_streak)}\n"
                f"Loss: {format_number(stats.current_loss_streak)}\n"
                f"Best Win: {format_number(stats.best_win_streak)}\n"
                f"Best Loss: {format_number(stats.best_loss_streak)}"
            ),
            inline=True,
        )
        embed.add_field(
            name="Coins",
            value=(
                f"Bet: {format_coin(stats.total_bet)}\n"
                f"Payout: {format_coin(stats.total_payout)}\n"
                f"Profit: {format_coin(stats.net_profit)}\n"
                f"Biggest Bet: {format_coin(stats.biggest_bet)}\n"
                f"Biggest Win: {format_coin(stats.biggest_win)}"
            ),
            inline=False,
        )
        unlocked = sum(1 for item in self.achievements if item.game_type == game_type)
        embed.add_field(name="Achievements", value=f"{format_number(unlocked)}/{format_number(AchievementService.game_count(game_type))}", inline=False)
        return embed

    def _achievements_embed(self) -> discord.Embed:
        embed = self._base_embed("Achievements")
        embed.add_field(
            name="Progress",
            value=f"Unlocked {format_number(len(self.achievements))}/{format_number(AchievementService.total_count())} achievements.",
            inline=False,
        )
        if not self.achievements:
            embed.add_field(name="Recent", value="No achievements unlocked yet.", inline=False)
            return embed
        lines = []
        for item in self.achievements[:10]:
            definition = AchievementService.definition(item.achievement_id)
            name = definition.name if definition else item.achievement_id
            lines.append(f"**{name}** — <t:{item.unlocked_at}:R>")
        embed.add_field(name="Recent", value="\n".join(lines), inline=False)
        return embed


def _stats_text(stats) -> str:
    win_rate = 0 if stats.total_games <= 0 else int(stats.wins * 100 / stats.total_games)
    return (
        f"Wins: {format_number(stats.wins)}\n"
        f"Losses: {format_number(stats.losses)}\n"
        f"Draws: {format_number(stats.draws)}\n"
        f"Games: {format_number(stats.total_games)}\n"
        f"Win Rate: {format_number(win_rate)}%"
    )


def _bot_name(bot: commands.Bot) -> str | None:
    return bot.user.display_name if bot.user is not None else None


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ProfileCog(bot))
