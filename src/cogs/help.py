from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from src.config import baucua as baucua_config
from src.config import blackjack as blackjack_config
from src.config import coinflip as coinflip_config
from src.config import lottery as lottery_config
from src.config import sicbo as sicbo_config
from src.config.emojis import (
    BUTTON_DOUBLE_EMOJI,
    BUTTON_HIT_EMOJI,
    BUTTON_STAND_EMOJI,
    COIN_EMOJI,
    COINFLIP_HEADS_EMOJI,
    COINFLIP_TAILS_EMOJI,
    BAUCUA_BOWL_EMOJI,
    SICBO_BOWL_EMOJI,
    RESULT_DRAW_EMOJI,
    RESULT_LOSE_EMOJI,
    RESULT_WIN_EMOJI,
    TICKET_EMOJI,
)
from src.utils.footer import random_footer_text
from src.utils.money import format_coin, format_number

HELP_PAGE_COUNT = 5


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="help", description="View casino game help.")
    @app_commands.describe(page="Help page number")
    async def slash_help(self, interaction: discord.Interaction, page: int = 1) -> None:
        page = _normalize_page(page)
        await interaction.response.send_message(embed=_help_embed(page), view=HelpView(interaction.user.id, page), ephemeral=True)

    @commands.command(name="help")
    async def prefix_help(self, ctx: commands.Context, page: int = 1) -> None:
        page = _normalize_page(page)
        await ctx.reply(embed=_help_embed(page), view=HelpView(ctx.author.id, page), mention_author=True)


class HelpView(discord.ui.View):
    def __init__(self, owner_id: int, page: int = 1) -> None:
        super().__init__(timeout=180)
        self.owner_id = owner_id
        self.page = page
        self._update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.owner_id:
            return True
        await interaction.response.send_message("This help menu is not yours.", ephemeral=True)
        return False

    @discord.ui.button(style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.page = HELP_PAGE_COUNT if self.page == 1 else self.page - 1
        self._update_buttons()
        await interaction.response.edit_message(embed=_help_embed(self.page), view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.page = 1 if self.page == HELP_PAGE_COUNT else self.page + 1
        self._update_buttons()
        await interaction.response.edit_message(embed=_help_embed(self.page), view=self)

    def _update_buttons(self) -> None:
        previous_page = HELP_PAGE_COUNT if self.page == 1 else self.page - 1
        next_page = 1 if self.page == HELP_PAGE_COUNT else self.page + 1
        self.previous_page.label = f"Previous: {_page_name(previous_page)}"
        self.previous_page.emoji = _page_emoji(previous_page)
        self.next_page.label = f"Next: {_page_name(next_page)}"
        self.next_page.emoji = _page_emoji(next_page)


def _page_name(page: int) -> str:
    names = {
        1: "Blackjack",
        2: "Coin Flip",
        3: "Lottery",
        4: "Sicbo",
        5: "Baucua",
    }
    return names[page]


def _page_emoji(page: int) -> str:
    emojis = {
        1: BUTTON_HIT_EMOJI,
        2: COINFLIP_HEADS_EMOJI,
        3: TICKET_EMOJI,
        4: SICBO_BOWL_EMOJI,
        5: BAUCUA_BOWL_EMOJI,
    }
    return emojis[page]


def _normalize_page(page: int) -> int:
    return min(max(page, 1), HELP_PAGE_COUNT)


def _help_embed(page: int) -> discord.Embed:
    page = _normalize_page(page)
    if page == 1:
        return _blackjack_help_embed()
    if page == 2:
        return _coinflip_help_embed()
    if page == 3:
        return _lottery_help_embed()
    if page == 4:
        return _sicbo_help_embed()
    return _baucua_help_embed()


def _blackjack_help_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Blackjack — Help",
        description=(
            "*Play against the dealer. Get closer to 21 without busting.*\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0x2B5EE8,
    )

    embed.add_field(
        name="How to play",
        value=(
            "`/bj bet <amount>`\n"
            "`!bj bet <amount>`\n"
            f"Minimum bet: {format_coin(blackjack_config.MIN_BET)}"
            f"{_max_bet_text(blackjack_config.MAX_BET)}"
        ),
        inline=False,
    )

    embed.add_field(
        name="Actions",
        value=(
            f"{BUTTON_HIT_EMOJI} **Hit** — Draw one more card\n"
            f"{BUTTON_STAND_EMOJI} **Stand** — End your turn and let the dealer play\n"
            f"{BUTTON_DOUBLE_EMOJI} **Double** — Double the bet, draw 1 card, then auto Stand\n"
            f"Dealer stands at: **{format_number(blackjack_config.DEALER_STAND_SCORE)}** points"
        ),
        inline=False,
    )

    embed.add_field(
        name="Results",
        value=(
            f"{RESULT_WIN_EMOJI} **Win** — Receive bet x{format_number(blackjack_config.NORMAL_WIN_PAYOUT_MULTIPLIER)} {COIN_EMOJI}\n"
            f"{RESULT_WIN_EMOJI} **Blackjack!** — Receive bet x{format_number(blackjack_config.BLACKJACK_PAYOUT_MULTIPLIER)} {COIN_EMOJI}\n"
            f"{RESULT_DRAW_EMOJI} **Draw** — Receive bet x{format_number(blackjack_config.DRAW_PAYOUT_MULTIPLIER)} {COIN_EMOJI}\n"
            f"{RESULT_LOSE_EMOJI} **Lose** — Lose your bet"
        ),
        inline=False,
    )

    embed.set_footer(text=random_footer_text())
    return embed


def _coinflip_help_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Coin Flip — Help",
        description=(
            "*Pick a coin side, flip it, and wait for the result.*\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xF5A623,
    )

    embed.add_field(
        name="How to play",
        value=(
            "`/cf bet <h|t> <amount>`\n"
            "`!cf bet <h|t> <amount>`\n"
            f"Minimum bet: {format_coin(coinflip_config.MIN_BET)}"
            f"{_max_bet_text(coinflip_config.MAX_BET)}\n"
            f"Flip delay: {format_number(coinflip_config.RESOLVE_DELAY_MIN_SECONDS)}-{format_number(coinflip_config.RESOLVE_DELAY_MAX_SECONDS)} seconds"
        ),
        inline=False,
    )

    embed.add_field(
        name="Choices",
        value=(
            f"{COINFLIP_HEADS_EMOJI} **h / heads** — Heads\n"
            f"{COINFLIP_TAILS_EMOJI} **t / tails** — Tails"
        ),
        inline=False,
    )

    embed.add_field(
        name="Results",
        value=(
            f"{RESULT_WIN_EMOJI} **Win** — Receive bet x{format_number(coinflip_config.WIN_PAYOUT_MULTIPLIER)} {COIN_EMOJI}\n"
            f"{RESULT_LOSE_EMOJI} **Lose** — Lose your bet"
        ),
        inline=False,
    )

    embed.set_footer(text=random_footer_text())
    return embed


def _lottery_help_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Lottery — Help",
        description=(
            f"*Buy {TICKET_EMOJI} tickets, wait for the draw, and hope to hit the jackpot!*\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xFFD700,
    )

    embed.add_field(
        name="Commands",
        value=(
            f"{TICKET_EMOJI} **Buy a chosen number**\n"
            "`/lt buy <number> <quantity>`\n"
            "`!lt buy <number> <quantity>`\n\n"
            f"{TICKET_EMOJI} **Buy random tickets**\n"
            "`/lt random <quantity>`\n"
            "`!lt random <quantity>`\n\n"
            f"{TICKET_EMOJI} **View your tickets**\n"
            "`/lt tickets` or `!lt tickets`\n\n"
            f"{TICKET_EMOJI} **View current draw info**\n"
            "`/lt info` or `!lt info`\n\n"
            f"{TICKET_EMOJI} **Set announcement channel**\n"
            "`/lt set <channel>`\n"
            "`!lt set #channel`"
        ),
        inline=False,
    )

    embed.add_field(
        name="Config",
        value=(
            f"Ticket price: {format_coin(lottery_config.TICKET_PRICE)} per {TICKET_EMOJI}\n"
            f"Draw interval: **{format_number(lottery_config.DRAW_INTERVAL_SECONDS)} seconds**\n"
            f"Initial jackpot: {format_coin(lottery_config.INITIAL_JACKPOT_POOL)}\n"
            f"Max per purchase: **{format_number(lottery_config.MAX_TICKETS_PER_PURCHASE)}** {TICKET_EMOJI}\n"
            f"Max per user/draw: **{format_number(lottery_config.MAX_TICKETS_PER_USER_PER_DRAW)}** {TICKET_EMOJI}"
        ),
        inline=False,
    )

    embed.add_field(
        name="Winning rules",
        value=(
            f"Valid numbers: **{lottery_config.NUMBER_MIN:0{lottery_config.NUMBER_DIGITS}d}-{lottery_config.NUMBER_MAX:0{lottery_config.NUMBER_DIGITS}d}**\n"
            "Input `1` becomes `0001`; input `12` becomes `0012`\n"
            f"{RESULT_WIN_EMOJI} Match **last 1 digit** — {format_coin(_lottery_fixed_payout(1))}\n"
            f"{RESULT_WIN_EMOJI} Match **last 2 digits** — {format_coin(_lottery_fixed_payout(2))}\n"
            f"{RESULT_WIN_EMOJI} Match **last 3 digits** — {format_coin(_lottery_fixed_payout(3))}\n"
            f"{RESULT_WIN_EMOJI} Match **all 4 digits** — **JACKPOT** {COIN_EMOJI}"
        ),
        inline=False,
    )

    embed.set_footer(text=random_footer_text())
    return embed


def _sicbo_help_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Sicbo — Help",
        description=(
            "*Bet on Big or Small before the round closes.*\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0x8E44AD,
    )

    embed.add_field(
        name="Commands",
        value=(
            "**Place a bet**\n"
            "`/sb bet <big|small> <amount>`\n"
            "`!sb bet <tai|xiu> <amount>`\n\n"
            "**View current round**\n"
            "`/sb info` or `!sb info`\n\n"
            "**Set round channel**\n"
            "`/sb set <channel>`\n"
            "`!sb set #channel`"
        ),
        inline=False,
    )

    embed.add_field(
        name="Config",
        value=(
            f"Minimum bet: {format_coin(sicbo_config.MIN_BET)}"
            f"{_max_bet_text(sicbo_config.MAX_BET)}\n"
            f"Round time: **{format_number(sicbo_config.ROUND_SECONDS)} seconds**\n"
            f"Win payout: bet x{format_number(sicbo_config.PAYOUT_MULTIPLIER)} {COIN_EMOJI}"
        ),
        inline=False,
    )

    embed.add_field(
        name="Winning rules",
        value=(
            f"{RESULT_WIN_EMOJI} **Big** wins on total **11-17**\n"
            f"{RESULT_WIN_EMOJI} **Small** wins on total **4-10**\n"
            f"{RESULT_LOSE_EMOJI} Total **3** or **18** means the house wins and both sides lose."
        ),
        inline=False,
    )

    embed.set_footer(text=random_footer_text())
    return embed


def _baucua_help_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Baucua — Help",
        description=(
            "*Bet on Deer, Pear, Chicken, Fish, Crab, or Shrimp before the round closes.*\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xE67E22,
    )

    embed.add_field(
        name="Commands",
        value=(
            "**Place a bet**\n"
            "`/bc bet <choice> <amount>`\n"
            "`!bc bet <choice> <amount>`\n"
            "`!baucua bet <choice> <amount>`\n\n"
            "**View current round**\n"
            "`/bc info` or `!bc info`\n\n"
            "**Set round channel**\n"
            "`/bc set <channel>`\n"
            "`!bc set #channel`"
        ),
        inline=False,
    )

    embed.add_field(
        name="Config",
        value=(
            f"Minimum bet: {format_coin(baucua_config.MIN_BET)}"
            f"{_max_bet_text(baucua_config.MAX_BET)}\n"
            f"Round time: **{format_number(baucua_config.ROUND_SECONDS)} seconds**\n"
            f"Payout per hit: bet x{format_number(baucua_config.PAYOUT_MULTIPLIER)} {COIN_EMOJI}"
        ),
        inline=False,
    )

    embed.add_field(
        name="Winning rules",
        value=(
            f"{RESULT_WIN_EMOJI} Each matching symbol pays bet x{format_number(baucua_config.PAYOUT_MULTIPLIER)}\n"
            "One matching symbol pays once, two matching symbols pay twice, and three matching symbols pay three times."
        ),
        inline=False,
    )

    embed.set_footer(text=random_footer_text())
    return embed


def _max_bet_text(max_bet: int | None) -> str:
    if max_bet is None:
        return ""
    return f"\nMaximum bet: {format_coin(max_bet)}"


def _lottery_fixed_payout(matched_digits: int) -> int:
    ev = 1 - lottery_config.JACKPOT_CONTRIBUTION_RATE - lottery_config.HOUSE_EDGE_RATE
    if matched_digits == 1:
        return int(lottery_config.TICKET_PRICE * 10 * ev)
    if matched_digits == 2:
        return int(lottery_config.TICKET_PRICE * 100 * ev)
    if matched_digits == 3:
        return int(lottery_config.TICKET_PRICE * 1000 * ev)
    return 0


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))