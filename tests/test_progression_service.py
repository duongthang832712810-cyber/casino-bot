from src.config.emojis import (
    PROGRESS_BAR_LEFT_FULL_EMOJI,
    PROGRESS_BAR_MIDDLE_EMPTY_EMOJI,
    PROGRESS_BAR_MIDDLE_FULL_EMOJI,
    PROGRESS_BAR_RIGHT_EMPTY_EMOJI,
)
from src.core.constants import RESULT_DRAW, RESULT_LOSE, RESULT_WIN
from src.services.progression_service import ProgressionService


def test_required_exp_uses_growth_floor() -> None:
    assert ProgressionService.required_exp_for_level(0) == 100
    assert ProgressionService.required_exp_for_level(1) == 110
    assert ProgressionService.required_exp_for_level(2) == 121
    assert ProgressionService.required_exp_for_level(3) == 133


def test_positive_exp_can_level_up_with_remainder() -> None:
    update = ProgressionService.apply_exp_delta(level=0, exp=90, exp_delta=25)
    assert update.new_level == 1
    assert update.new_exp == 15


def test_negative_exp_can_level_down_with_remainder() -> None:
    update = ProgressionService.apply_exp_delta(level=2, exp=10, exp_delta=-30)
    assert update.new_level == 1
    assert update.new_exp == 90


def test_level_zero_exp_never_goes_below_zero() -> None:
    update = ProgressionService.apply_exp_delta(level=0, exp=10, exp_delta=-30)
    assert update.new_level == 0
    assert update.new_exp == 0


def test_exp_delta_uses_common_rates() -> None:
    assert ProgressionService.exp_delta_for_result(100, RESULT_WIN) == 20
    assert ProgressionService.exp_delta_for_result(100, RESULT_LOSE) == -10
    assert ProgressionService.exp_delta_for_result(100, RESULT_DRAW) == -2


def test_level_progress_uses_custom_progress_bar_emojis() -> None:
    progress = ProgressionService.level_progress(level=0, exp=50)
    assert progress.bar == (
        PROGRESS_BAR_LEFT_FULL_EMOJI
        + (PROGRESS_BAR_MIDDLE_FULL_EMOJI * 4)
        + (PROGRESS_BAR_MIDDLE_EMPTY_EMOJI * 4)
        + PROGRESS_BAR_RIGHT_EMPTY_EMOJI
    )
