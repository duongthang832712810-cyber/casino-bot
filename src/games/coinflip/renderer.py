from __future__ import annotations

import discord

from src.config.emojis import (
    COIN_ICON_URL,
    RESULT_LOSE_ICON_URL,
    RESULT_WIN_ICON_URL,
)
from src.core.constants import RESULT_LOSE, RESULT_WIN
from src.games.coinflip.constants import CHOICE_HEADS
from src.games.coinflip.models import CoinFlipActionResult, CoinFlipGame
from src.utils.footer import random_footer_text
from src.utils.money import format_coin


def render_coinflip_embed(
    game: CoinFlipGame,
    player: discord.abc.User,
    *,
    finished: bool = False,
    outcome: str | None = None,
    result: str | None = None,
    net: int = 0,
    footer_text: str | None = None,
) -> discord.Embed:
    embed = discord.Embed(color=_embed_color(finished, result))
    embed.set_author(name=f"{player.display_name}'s Coin Flip", icon_url=player.display_avatar.url)

    result_display = _result_display(finished, result, net)

    embed.add_field(name="Bet", value=format_coin(game.bet_amount), inline=True)
    embed.add_field(name="Pick", value=_choice_label(game.choice), inline=True)
    embed.add_field(name="Result", value=result_display, inline=True)

    embed.set_footer(text=footer_text or random_footer_text(), icon_url=_footer_icon_url(finished, outcome, result))
    return embed


def render_from_action(
    action: CoinFlipActionResult,
    player: discord.abc.User,
    *,
    footer_text: str | None = None,
) -> discord.Embed:
    return render_coinflip_embed(
        action.game,
        player,
        finished=action.finished,
        outcome=action.outcome,
        result=action.result,
        net=action.net,
        footer_text=footer_text,
    )


def _choice_label(choice: str) -> str:
    return "Heads" if choice == CHOICE_HEADS else "Tails"


def _result_display(finished: bool, result: str | None, net: int) -> str:
    if not finished or result is None:
        return "Flipping..."
    if result == RESULT_WIN:
        return f"Won +{format_coin(net)}"
    return f"Lost {format_coin(net)}"


def _embed_color(finished: bool, result: str | None) -> discord.Color:
    if not finished:
        return discord.Color.blue()
    return discord.Color.green() if result == RESULT_WIN else discord.Color.red()


def _footer_icon_url(finished: bool, outcome: str | None, result: str | None) -> str:
    if not finished or outcome is None:
        return COIN_ICON_URL
    if result == RESULT_WIN:
        return RESULT_WIN_ICON_URL
    if result == RESULT_LOSE:
        return RESULT_LOSE_ICON_URL
    return COIN_ICON_URL
