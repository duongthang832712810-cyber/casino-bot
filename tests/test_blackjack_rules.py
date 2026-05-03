from src.games.blackjack.rules import compare_hands, dealer_play


def test_compare_win():
    assert compare_hands(["10S", "9H"], ["10D", "8C"]) == "win"


def test_compare_lose():
    assert compare_hands(["10S", "7H"], ["10D", "8C"]) == "lose"


def test_compare_draw():
    assert compare_hands(["10S", "8H"], ["10D", "8C"]) == "draw"


def test_dealer_draw_until_17():
    dealer = ["2S", "3H"]
    deck = ["4D", "8C", "KS"]
    dealer_play(dealer, deck)
    assert dealer == ["2S", "3H", "4D", "8C"]
