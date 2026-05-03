from __future__ import annotations

import discord

from src.config.emojis import BLACKJACK_CARD_EMOJIS, LOADING_ICON_URL, RESULT_DRAW_ICON_URL, RESULT_LOSE_ICON_URL, RESULT_WIN_ICON_URL
from src.core.constants import RESULT_BLACKJACK, RESULT_LOSE, RESULT_WIN
from src.games.blackjack.deck import cards_to_emojis, cards_to_symbols, card_to_emoji, card_to_symbol
from src.games.blackjack.models import BlackjackActionResult, BlackjackGame
from src.utils.footer import random_footer_text
from src.utils.money import format_coin

ZERO_WIDTH = "\u200b"


def render_blackjack_embed(
    game: BlackjackGame,
    player: discord.abc.User,
    *,
    finished: bool = False,
    result: str | None = None,
    net: int = 0,
    footer_text: str | None = None,
) -> discord.Embed:
    embed = discord.Embed(color=_embed_color(finished, result))
    embed.set_author(name=f"{player.display_name}'s Blackjack Game", icon_url=player.display_avatar.url)

    player_emoji_line = cards_to_emojis(game.player_cards)
    player_symbol_line = cards_to_symbols(game.player_cards)

    if finished:
        dealer_emoji_line = cards_to_emojis(game.dealer_cards)
        dealer_symbol_line = cards_to_symbols(game.dealer_cards)
    else:
        dealer_emoji_line, dealer_symbol_line = _hidden_dealer_lines(game)

    result_line = _format_result_line(finished, result, net)

    embed.add_field(name=ZERO_WIDTH, value="Player\nDealer\n\nBet\nResult", inline=True)
    embed.add_field(
        name=ZERO_WIDTH,
        value=f"{player_emoji_line}\n{dealer_emoji_line}\n\n{format_coin(game.bet_amount)}\n{result_line}",
        inline=True,
    )
    embed.add_field(name=ZERO_WIDTH, value=f"{player_symbol_line}\n{dealer_symbol_line}", inline=True)

    footer = footer_text or random_footer_text()
    footer_icon_url = _footer_icon_url(finished, result)
    embed.set_footer(text=footer, icon_url=footer_icon_url)
    return embed


def render_from_action(action: BlackjackActionResult, player: discord.abc.User, *, footer_text: str | None = None) -> discord.Embed:
    return render_blackjack_embed(
        action.game,
        player,
        finished=action.finished,
        result=action.result,
        net=action.net,
        footer_text=footer_text,
    )


def content_for_player(user_id: str, finished: bool) -> str:
    return ""


def _hidden_dealer_lines(game: BlackjackGame) -> tuple[str, str]:
    if not game.dealer_cards:
        return BLACKJACK_CARD_EMOJIS["BACK"], "??"
    first = game.dealer_cards[0]
    return f"{card_to_emoji(first)} {BLACKJACK_CARD_EMOJIS['BACK']}", f"{card_to_symbol(first)} ??"


def _embed_color(finished: bool, result: str | None) -> discord.Color:
    if not finished:
        return discord.Color.blue()
    if result in {RESULT_WIN, RESULT_BLACKJACK}:
        return discord.Color.green()
    if result == RESULT_LOSE:
        return discord.Color.red()
    return discord.Color.yellow()


def _format_result_line(finished: bool, result: str | None, net: int) -> str:
    if not finished or result is None:
        return "Playing..."
    if result == RESULT_BLACKJACK:
        return f"Blackjack +{format_coin(net)}"
    if result == RESULT_WIN:
        return f"Won +{format_coin(net)}"
    if result == RESULT_LOSE:
        return f"Lost {format_coin(net)}"
    return f"Push +{format_coin(0)}"


def _footer_icon_url(finished: bool, result: str | None) -> str | None:
    if not finished or result is None:
        return LOADING_ICON_URL
    if result in {RESULT_WIN, RESULT_BLACKJACK}:
        return RESULT_WIN_ICON_URL
    if result == RESULT_LOSE:
        return RESULT_LOSE_ICON_URL
    return RESULT_DRAW_ICON_URL
