from __future__ import annotations

from enum import StrEnum


class GameType(StrEnum):
    BLACKJACK = "blackjack"


class GameResult(StrEnum):
    BLACKJACK = "blackjack"
    WIN = "win"
    LOSE = "lose"
    DRAW = "draw"
