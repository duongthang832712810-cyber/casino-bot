from __future__ import annotations

from src.games.blackjack.constants import CARD_VALUES
from src.games.blackjack.deck import split_card


def calculate_score(cards: list[str]) -> int:
    total = 0
    aces = 0
    for card in cards:
        rank, _ = split_card(card)
        total += CARD_VALUES[rank]
        if rank == "A":
            aces += 1

    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    return total


def is_bust(cards: list[str]) -> bool:
    return calculate_score(cards) > 21


def is_blackjack(cards: list[str]) -> bool:
    if len(cards) != 2:
        return False
    ranks = [split_card(card)[0] for card in cards]
    return "A" in ranks and any(rank in {"10", "J", "Q", "K"} for rank in ranks)
