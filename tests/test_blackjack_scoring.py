from src.games.blackjack.scoring import calculate_score, is_blackjack, is_bust


def test_ace_scores_as_eleven_when_safe():
    assert calculate_score(["AS", "9H"]) == 20


def test_ace_scores_as_one_when_needed():
    assert calculate_score(["AS", "9H", "5D"]) == 15


def test_two_aces():
    assert calculate_score(["AS", "AH", "9D"]) == 21


def test_bust():
    assert is_bust(["10S", "KH", "2D"])


def test_blackjack():
    assert is_blackjack(["AS", "KH"])
    assert not is_blackjack(["AS", "KH", "2D"])
