from __future__ import annotations

from src.config.emojis import COIN_EMOJI


def format_number(amount: int) -> str:
    return f"{amount:,}"


def format_coin(amount: int) -> str:
    return f"{format_number(amount)} {COIN_EMOJI}"
