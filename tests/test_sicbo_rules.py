from src.games.sicbo.constants import CHOICE_BIG, CHOICE_SMALL, RESULT_HOUSE
from src.games.sicbo.rules import normalize_choice, result_for_total


def test_sicbo_total_3_and_18_are_house_wins() -> None:
    assert result_for_total(3) == RESULT_HOUSE
    assert result_for_total(18) == RESULT_HOUSE


def test_sicbo_total_4_to_10_is_small() -> None:
    for total in range(4, 11):
        assert result_for_total(total) == CHOICE_SMALL


def test_sicbo_total_11_to_17_is_big() -> None:
    for total in range(11, 18):
        assert result_for_total(total) == CHOICE_BIG


def test_sicbo_choice_aliases_are_normalized() -> None:
    assert normalize_choice("big") == CHOICE_BIG
    assert normalize_choice("b") == CHOICE_BIG
    assert normalize_choice("tai") == CHOICE_BIG
    assert normalize_choice("small") == CHOICE_SMALL
    assert normalize_choice("s") == CHOICE_SMALL
    assert normalize_choice("xiu") == CHOICE_SMALL
