from __future__ import annotations

from src.core.errors import InvalidBetAmountError
from src.games.baucua.constants import CHOICE_ALIASES


def normalize_choice(raw_choice: str) -> str:
    choice = CHOICE_ALIASES.get(raw_choice.strip().lower())
    if choice is None:
        raise InvalidBetAmountError("Choice must be deer, pear, chicken, fish, crab, or shrimp.")
    return choice
