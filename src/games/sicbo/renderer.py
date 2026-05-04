from __future__ import annotations

import discord

from src.config import sicbo as sicbo_config
from src.config.emojis import SICBO_BOWL_ROWS, SICBO_DICE_EMOJIS
from src.games.sicbo.constants import CHOICE_BIG, CHOICE_DISPLAY, CHOICE_SMALL, STATUS_BETTING
from src.games.sicbo.models import SicboBet, SicboState
from src.utils.footer import random_footer_text
from src.utils.money import format_coin, format_number

ZERO_WIDTH = "\u200b"


def render_sicbo_embed(state: SicboState, bets: list[SicboBet], bot_name: str | None = None) -> discord.Embed:
    embed = discord.Embed(
        title=f"Sicbo Round #{format_number(state.round_id)}",
        color=0x8E44AD if state.status == STATUS_BETTING else 0x2ECC71,
    )
    if state.status == STATUS_BETTING:
        embed.description = f"Betting closes in <t:{state.ends_at}:R>."
    else:
        embed.description = "Betting is closed."

    embed.add_field(name="Total Big Bets", value=_choice_field_value(state, bets, CHOICE_BIG), inline=True)
    embed.add_field(name=ZERO_WIDTH, value=_middle_field_value(state), inline=True)
    embed.add_field(name="Total Small Bets", value=_choice_field_value(state, bets, CHOICE_SMALL), inline=True)
    embed.set_footer(text=random_footer_text(bot_name))
    return embed


def _choice_field_value(state: SicboState, bets: list[SicboBet], choice: str) -> str:
    choice_bets = [bet for bet in bets if bet.choice == choice]
    total = sum(bet.amount for bet in choice_bets)
    label = "Big bettors" if choice == CHOICE_BIG else "Small bettors"
    lines = [format_coin(total), "", label]

    if state.status != STATUS_BETTING and state.result != choice:
        lines.append("No winning bets shown.")
        return "\n".join(lines)

    if not choice_bets:
        lines.append("No bets yet.")
        return "\n".join(lines)

    for bet in choice_bets[: sicbo_config.MAX_DISPLAYED_BETTORS]:
        lines.append(f"<@{bet.user_id}> — {format_coin(bet.amount)}")

    remaining = len(choice_bets) - sicbo_config.MAX_DISPLAYED_BETTORS
    if remaining > 0:
        lines.append(f"and {format_number(remaining)} more...")

    return "\n".join(lines)


def _middle_field_value(state: SicboState) -> str:
    if state.status == STATUS_BETTING:
        return "\n".join("".join(row) for row in SICBO_BOWL_ROWS)

    dice_values = (state.dice_1, state.dice_2, state.dice_3)
    if any(value is None for value in dice_values) or state.result is None:
        return "Result: Unknown"

    dice = tuple(int(value) for value in dice_values if value is not None)
    dice_line = " ".join(SICBO_DICE_EMOJIS[value] for value in dice)
    total = sum(dice)
    result_text = CHOICE_DISPLAY.get(state.result, "Unknown")
    return f"Result: {result_text}\n{dice_line}\nTotal: {format_number(total)}"
