from __future__ import annotations

from collections import Counter

import discord

from src.config import baucua as baucua_config
from src.config.emojis import BAUCUA_PIECE_ROWS, BAUCUA_SYMBOL_EMOJIS
from src.games.baucua.constants import CHOICE_DISPLAY, CHOICES, STATUS_BETTING
from src.games.baucua.models import BaucuaBet, BaucuaState
from src.utils.footer import random_footer_text
from src.utils.money import format_coin, format_number

ZERO_WIDTH = "\u200b"
CHOICE_FIELD_ORDER = ("deer", "pear", "chicken", "fish", "crab", "shrimp")


def render_baucua_embed(state: BaucuaState, bets: list[BaucuaBet], bot_name: str | None = None) -> discord.Embed:
    embed = discord.Embed(
        title=f"Baucua Round #{format_number(state.round_id)}",
        color=0xE67E22 if state.status == STATUS_BETTING else 0x2ECC71,
    )
    if state.status == STATUS_BETTING:
        embed.description = f"Betting closes in <t:{state.ends_at}:R>."
    else:
        embed.description = "Betting is closed."

    for choice in CHOICE_FIELD_ORDER[:3]:
        embed.add_field(name=CHOICE_DISPLAY[choice], value=_choice_field_value(state, bets, choice), inline=True)
    for choice in CHOICE_FIELD_ORDER[3:]:
        embed.add_field(name=CHOICE_DISPLAY[choice], value=_choice_field_value(state, bets, choice), inline=True)
    embed.add_field(name=ZERO_WIDTH, value=ZERO_WIDTH, inline=True)
    embed.add_field(name="Result", value=_middle_field_value(state), inline=True)
    embed.add_field(name=ZERO_WIDTH, value=ZERO_WIDTH, inline=True)
    embed.set_footer(text=random_footer_text(bot_name))
    return embed


def _choice_field_value(state: BaucuaState, bets: list[BaucuaBet], choice: str) -> str:
    lines = [*_piece_lines(choice), ""]
    choice_bets = [bet for bet in bets if bet.choice == choice]
    if state.status != STATUS_BETTING:
        hit_count = _result_counts(state).get(choice, 0)
        if hit_count <= 0:
            return "\n".join(lines).rstrip()
        for bet in choice_bets[: baucua_config.MAX_DISPLAYED_BETTORS]:
            payout = bet.amount * baucua_config.PAYOUT_MULTIPLIER * hit_count
            lines.append(f"<@{bet.user_id}> — +{format_coin(payout)}")
        remaining = len(choice_bets) - baucua_config.MAX_DISPLAYED_BETTORS
        if remaining > 0:
            lines.append(f"and {format_number(remaining)} more...")
        return "\n".join(lines).rstrip()

    if not choice_bets:
        return "\n".join(lines).rstrip()
    for bet in choice_bets[: baucua_config.MAX_DISPLAYED_BETTORS]:
        lines.append(f"<@{bet.user_id}> — {format_coin(bet.amount)}")
    remaining = len(choice_bets) - baucua_config.MAX_DISPLAYED_BETTORS
    if remaining > 0:
        lines.append(f"and {format_number(remaining)} more...")
    return "\n".join(lines)


def _piece_lines(choice: str) -> list[str]:
    return ["".join(row) for row in BAUCUA_PIECE_ROWS[choice]]


def _middle_field_value(state: BaucuaState) -> str:
    if state.status == STATUS_BETTING:
        return "\n".join("".join(row) for row in BAUCUA_PIECE_ROWS["bowl"])
    results = (state.result_1, state.result_2, state.result_3)
    if any(result is None for result in results):
        return "Unknown"
    result_line = " ".join(BAUCUA_SYMBOL_EMOJIS[str(result)] for result in results)
    return f"{ZERO_WIDTH}\n{result_line}\n{ZERO_WIDTH}"


def _result_counts(state: BaucuaState) -> Counter[str]:
    return Counter(result for result in (state.result_1, state.result_2, state.result_3) if result in CHOICES)
