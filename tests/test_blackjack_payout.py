from src.games.common.payout import blackjack_payout


def test_blackjack_payout():
    assert blackjack_payout(100, "blackjack") == (300, 200)


def test_win_payout():
    assert blackjack_payout(100, "win") == (200, 100)


def test_lose_payout():
    assert blackjack_payout(100, "lose") == (0, -100)


def test_draw_payout():
    assert blackjack_payout(100, "draw") == (100, 0)
