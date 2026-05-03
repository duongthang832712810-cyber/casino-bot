from __future__ import annotations

from math import floor

from src.config import blackjack as bj_config


class ExpService:
    @staticmethod
    def exp_delta_for_result(bet: int, result: str) -> int:
        if result in {"win", "blackjack"}:
            return floor(bet * bj_config.EXP_WIN_RATE)
        if result == "lose":
            return -floor(bet * bj_config.EXP_LOSE_RATE)
        if result == "draw":
            return -floor(bet * bj_config.EXP_DRAW_RATE)
        return 0
