from __future__ import annotations

from src.core.errors import InvalidBetAmountError
from src.games.sicbo.constants import CHOICE_ALIASES, CHOICE_BIG, CHOICE_SMALL, RESULT_HOUSE


def normalize_choice(raw_choice: str) -> str:
    choice = CHOICE_ALIASES.get(raw_choice.lower().strip())
    if choice is None:
        raise InvalidBetAmountError("Choose big/tai or small/xiu.")
    return choice


def result_for_total(total: int) -> str:
    if total in {3, 18}:
        return RESULT_HOUSE
    if 4 <= total <= 10:
        return CHOICE_SMALL
    return CHOICE_BIG
