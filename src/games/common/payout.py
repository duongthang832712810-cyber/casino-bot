from __future__ import annotations

from src.config import blackjack as bj_config


def blackjack_payout(bet: int, result: str) -> tuple[int, int]:
    if result == "blackjack":
        payout = bet * bj_config.BLACKJACK_PAYOUT_MULTIPLIER
        return payout, bet * (bj_config.BLACKJACK_PAYOUT_MULTIPLIER - 1)
    if result == "win":
        payout = bet * bj_config.NORMAL_WIN_PAYOUT_MULTIPLIER
        return payout, bet
    if result == "draw":
        payout = bet * bj_config.DRAW_PAYOUT_MULTIPLIER
        return payout, 0
    return 0, -bet
