from __future__ import annotations

import random

from src.config import blackjack as bj_config
from src.config.emojis import BLACKJACK_CARD_EMOJIS
from src.games.blackjack.constants import RANKS, SUIT_SYMBOLS, SUITS


def create_deck() -> list[str]:
    return [f"{rank}{suit}" for suit in SUITS for rank in RANKS]


def shuffle_deck(cards: list[str]) -> list[str]:
    shuffled = cards[:]
    random.shuffle(shuffled)
    return shuffled


def deal_initial_game() -> tuple[list[str], list[str], list[str]]:
    deck = shuffle_deck(create_deck())
    player_cards = [deck.pop(0), deck.pop(0)]
    dealer_cards = [deck.pop(0), deck.pop(0)]
    saved_deck = deck[: bj_config.SAVED_DECK_SIZE]
    return player_cards, dealer_cards, saved_deck


def pop_card(deck: list[str]) -> str:
    if not deck:
        raise RuntimeError("Deck is empty")
    return deck.pop(0)


def split_card(card: str) -> tuple[str, str]:
    return card[:-1], card[-1]


def card_to_symbol(card: str) -> str:
    rank, suit = split_card(card)
    return f"{rank}{SUIT_SYMBOLS[suit]}"


def cards_to_symbols(cards: list[str]) -> str:
    return " ".join(card_to_symbol(card) for card in cards)


def card_to_emoji(card: str) -> str:
    return BLACKJACK_CARD_EMOJIS.get(card, card_to_symbol(card))


def cards_to_emojis(cards: list[str]) -> str:
    return " ".join(card_to_emoji(card) for card in cards)
