from __future__ import annotations

from enum import Enum


class GameType(str, Enum):
    BLACKJACK = "blackjack"
    COINFLIP = "coinflip"
    LOTTERY = "lottery"
    SICBO = "sicbo"
    BAUCUA = "baucua"


class GameResult(str, Enum):
    BLACKJACK = "blackjack"
    WIN = "win"
    LOSE = "lose"
    DRAW = "draw"
    HOUSE = "house"
