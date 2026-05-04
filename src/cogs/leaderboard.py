from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from src.config.achievements import GAME_NAMES, GAME_TYPES
from src.config.emojis import TOP_RANK_EMOJIS
from src.config.leaderboard import CATEGORIES, CATEGORY_ACHIEVEMENTS, CATEGORY_BET, CATEGORY_COINS, CATEGORY_LEVEL, CATEGORY_PROFIT, CATEGORY_WINS
from src.utils.footer import random_footer_text
from src.utils.money import format_coin, format_number
from src.utils.rank import format_ranked_level

GAME_CHOICES = ("all", *GAME_TYPES)
CATEGORY_ALIASES = {
    "coin": CATEGORY_COINS,
    "coins": CATEGORY_COINS,
    "bal": CATEGORY_COINS,
    "balance": CATEGORY_COINS,
    "money": CATEGORY_COINS,
    "level": CATEGORY_LEVEL,
    "lvl": CATEGORY_LEVEL,
    "lv": CATEGORY_LEVEL,
    "wins": CATEGORY_WINS,
    "win": CATEGORY_WINS,
    "profit": CATEGORY_PROFIT,
    "net": CATEGORY_PROFIT,
    "netprofit": CATEGORY_PROFIT,
    "bet": CATEGORY_BET,
    "bets": CATEGORY_BET,
    "totalbet": CATEGORY_BET,
    "achievements": CATEGORY_ACHIEVEMENTS,
    "achievement": CATEGORY_ACHIEVEMENTS,
    "achieve": CATEGORY_ACHIEVEMENTS,
    "ach": CATEGORY_ACHIEVEMENTS,
}
GAME_ALIASES = {
    "all": None,
    "blackjack": "blackjack",
    "bj": "blackjack",
    "coinflip": "coinflip",
    "cf": "coinflip",
    "lottery": "lottery",
    "lt": "lottery",
    "ticket": "lottery",
    "tickets": "lottery",
    "sicbo": "sicbo",
    "sb": "sicbo",
    "tai": "sicbo",
    "xiu": "sicbo",
    "baucua": "baucua",
    "bc": "baucua",
}
class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="top", description="View casino leaderboards.")
    @app_commands.describe(category="coins/level/wins/profit/bet/achievements", game="all or a game name")
    async def slash_top(self, interaction: discord.Interaction, category: str = CATEGORY_COINS, game: str = "all") -> None:
        await interaction.response.send_message(embed=await self._embed(category, game), ephemeral=False)

    @commands.command(name="top")
    async def prefix_top(self, ctx: commands.Context, category: str = CATEGORY_COINS, game: str = "all") -> None:
        await ctx.reply(embed=await self._embed(category, game), mention_author=True)

    async def _embed(self, raw_category: str, raw_game: str) -> discord.Embed:
        category = _normalize_category(raw_category)
        game = _normalize_game(raw_game)
        service = self.bot.leaderboard_service  # type: ignore[attr-defined]
        rows = await service.top(category, game)
        title = _title(category, game)
        embed = discord.Embed(title=title, color=discord.Color.blurple())
        leaderboard_text = "No leaderboard data yet."
        if rows:
            leaderboard_text = "\n".join(
                f"{_top_prefix(index)} <@{user_id}> — {_format_value(category, value)}"
                for index, (user_id, value) in enumerate(rows, start=1)
            )
        embed.description = leaderboard_text
        embed.set_footer(text=random_footer_text(_bot_name(self.bot)))
        return embed


def _normalize_category(category: str) -> str:
    value = category.lower().strip().replace(" ", "")
    return CATEGORY_ALIASES.get(value, value if value in CATEGORIES else CATEGORY_COINS)


def _normalize_game(game: str) -> str | None:
    value = game.lower().strip().replace(" ", "")
    if value in GAME_ALIASES:
        return GAME_ALIASES[value]
    return value if value in GAME_CHOICES else None


def _title(category: str, game: str | None) -> str:
    category_name = {
        CATEGORY_COINS: "Coins",
        CATEGORY_LEVEL: "Level",
        CATEGORY_WINS: "Wins",
        CATEGORY_PROFIT: "Profit",
        CATEGORY_BET: "Bet",
        CATEGORY_ACHIEVEMENTS: "Achievements",
    }[category]
    if game is None or category in {CATEGORY_COINS, CATEGORY_LEVEL, CATEGORY_ACHIEVEMENTS}:
        return f"Top {category_name}"
    return f"Top {category_name} — {GAME_NAMES.get(game, game.title())}"


def _top_prefix(index: int) -> str:
    return TOP_RANK_EMOJIS.get(index, f"**{index}.**")


def _format_value(category: str, value: int) -> str:
    if category in {CATEGORY_COINS, CATEGORY_PROFIT, CATEGORY_BET}:
        return format_coin(value)
    if category == CATEGORY_LEVEL:
        return format_ranked_level(value)
    return format_number(value)


def _bot_name(bot: commands.Bot) -> str | None:
    return bot.user.display_name if bot.user is not None else None


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LeaderboardCog(bot))
