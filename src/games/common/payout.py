from __future__ import annotations

from src.config import blackjack as bj_config
from src.core.constants import RESULT_BLACKJACK, RESULT_DRAW, RESULT_WIN


def blackjack_payout(bet: int, result: str) -> tuple[int, int]:
    if result == RESULT_BLACKJACK:
        payout = bet * bj_config.BLACKJACK_PAYOUT_MULTIPLIER
        return payout, bet * (bj_config.BLACKJACK_PAYOUT_MULTIPLIER - 1)
    if result == RESULT_WIN:
        payout = bet * bj_config.NORMAL_WIN_PAYOUT_MULTIPLIER
        return payout, bet
    if result == RESULT_DRAW:
        payout = bet * bj_config.DRAW_PAYOUT_MULTIPLIER
        return payout, 0
    return 0, -bet
