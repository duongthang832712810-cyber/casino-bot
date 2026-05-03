from __future__ import annotations

from src.models.game import GameResult, GameType


GAME_BLACKJACK = GameType.BLACKJACK.value
GAME_COINFLIP = GameType.COINFLIP.value
GAME_LOTTERY = GameType.LOTTERY.value
GAME_SICBO = GameType.SICBO.value

RESULT_BLACKJACK = GameResult.BLACKJACK.value
RESULT_WIN = GameResult.WIN.value
RESULT_LOSE = GameResult.LOSE.value
RESULT_DRAW = GameResult.DRAW.value
RESULT_HOUSE = GameResult.HOUSE.value
