from src.core.constants import RESULT_BLACKJACK, RESULT_DRAW, RESULT_LOSE, RESULT_WIN
from src.games.common.payout import blackjack_payout


def test_blackjack_payout():
    assert blackjack_payout(100, RESULT_BLACKJACK) == (300, 200)


def test_win_payout():
    assert blackjack_payout(100, RESULT_WIN) == (200, 100)


def test_lose_payout():
    assert blackjack_payout(100, RESULT_LOSE) == (0, -100)


def test_draw_payout():
    assert blackjack_payout(100, RESULT_DRAW) == (100, 0)
