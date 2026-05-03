from __future__ import annotations

from src.config import blackjack as bj_config
from src.core.constants import RESULT_DRAW, RESULT_LOSE, RESULT_WIN
from src.games.blackjack.deck import pop_card
from src.games.blackjack.scoring import calculate_score, is_bust


def dealer_play(dealer_cards: list[str], deck: list[str]) -> None:
    while calculate_score(dealer_cards) < bj_config.DEALER_STAND_SCORE:
        dealer_cards.append(pop_card(deck))


def compare_hands(player_cards: list[str], dealer_cards: list[str]) -> str:
    if is_bust(player_cards):
        return RESULT_LOSE
    if is_bust(dealer_cards):
        return RESULT_WIN

    player_score = calculate_score(player_cards)
    dealer_score = calculate_score(dealer_cards)

    if player_score > dealer_score:
        return RESULT_WIN
    if player_score < dealer_score:
        return RESULT_LOSE
    return RESULT_DRAW
