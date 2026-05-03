from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR

from src.config import general as general_config
from src.config.emojis import (
    PROGRESS_BAR_LEFT_EMPTY_EMOJI,
    PROGRESS_BAR_LEFT_FULL_EMOJI,
    PROGRESS_BAR_MIDDLE_EMPTY_EMOJI,
    PROGRESS_BAR_MIDDLE_FULL_EMOJI,
    PROGRESS_BAR_RIGHT_EMPTY_EMOJI,
    PROGRESS_BAR_RIGHT_FULL_EMOJI,
)
from src.core.constants import RESULT_BLACKJACK, RESULT_DRAW, RESULT_LOSE, RESULT_WIN


@dataclass(frozen=True, slots=True)
class ProgressionUpdate:
    old_level: int
    old_exp: int
    new_level: int
    new_exp: int
    exp_delta: int

    @property
    def leveled_up(self) -> bool:
        return self.new_level > self.old_level

    @property
    def leveled_down(self) -> bool:
        return self.new_level < self.old_level

    @property
    def changed_level(self) -> bool:
        return self.new_level != self.old_level


@dataclass(frozen=True, slots=True)
class LevelProgress:
    level: int
    exp: int
    required_exp: int
    bar: str


class ProgressionService:
    @staticmethod
    def exp_delta_for_result(bet: int, result: str) -> int:
        rate = ProgressionService._rate_for_result(result)
        return ProgressionService.floor_decimal(Decimal(bet) * rate)

    @staticmethod
    def required_exp_for_level(level: int) -> int:
        level = max(0, level)
        value = Decimal(general_config.LEVEL_BASE_REQUIRED_EXP) * (general_config.LEVEL_REQUIRED_EXP_GROWTH ** level)
        return max(1, ProgressionService.floor_decimal(value))

    @staticmethod
    def apply_exp_delta(level: int, exp: int, exp_delta: int) -> ProgressionUpdate:
        old_level = max(0, level)
        old_exp = max(0, exp)
        new_level = old_level
        new_exp = old_exp + exp_delta

        if exp_delta >= 0:
            while new_exp >= ProgressionService.required_exp_for_level(new_level):
                new_exp -= ProgressionService.required_exp_for_level(new_level)
                new_level += 1
        else:
            while new_exp < 0 and new_level > 0:
                new_level -= 1
                new_exp += ProgressionService.required_exp_for_level(new_level)
            if new_exp < 0:
                new_exp = 0

        return ProgressionUpdate(
            old_level=old_level,
            old_exp=old_exp,
            new_level=new_level,
            new_exp=new_exp,
            exp_delta=exp_delta,
        )

    @staticmethod
    def level_progress(level: int, exp: int) -> LevelProgress:
        level = max(0, level)
        exp = max(0, exp)
        required_exp = ProgressionService.required_exp_for_level(level)
        filled = 0
        if required_exp > 0:
            filled = min(
                general_config.EXP_PROGRESS_BAR_WIDTH,
                ProgressionService.floor_decimal(
                    Decimal(exp) * Decimal(general_config.EXP_PROGRESS_BAR_WIDTH) / Decimal(required_exp)
                ),
            )
        return LevelProgress(
            level=level,
            exp=exp,
            required_exp=required_exp,
            bar=ProgressionService._progress_bar(filled, general_config.EXP_PROGRESS_BAR_WIDTH),
        )

    @staticmethod
    def _progress_bar(filled: int, width: int) -> str:
        width = max(2, width)
        filled = min(max(0, filled), width)
        parts: list[str] = []
        for index in range(width):
            is_filled = index < filled
            if index == 0:
                parts.append(PROGRESS_BAR_LEFT_FULL_EMOJI if is_filled else PROGRESS_BAR_LEFT_EMPTY_EMOJI)
            elif index == width - 1:
                parts.append(PROGRESS_BAR_RIGHT_FULL_EMOJI if is_filled else PROGRESS_BAR_RIGHT_EMPTY_EMOJI)
            else:
                parts.append(PROGRESS_BAR_MIDDLE_FULL_EMOJI if is_filled else PROGRESS_BAR_MIDDLE_EMPTY_EMOJI)
        return "".join(parts)

    @staticmethod
    def level_change_message(user_id: str, update: ProgressionUpdate | None) -> str | None:
        if update is None or not update.changed_level:
            return None
        if update.leveled_up:
            return f"<@{user_id}> leveled up from Lv.{update.old_level} to Lv.{update.new_level}."
        return f"<@{user_id}> dropped from Lv.{update.old_level} to Lv.{update.new_level}."

    @staticmethod
    def floor_decimal(value: Decimal) -> int:
        return int(value.to_integral_value(rounding=ROUND_FLOOR))

    @staticmethod
    def _rate_for_result(result: str) -> Decimal:
        if result in {RESULT_WIN, RESULT_BLACKJACK}:
            return general_config.EXP_WIN_RATE
        if result == RESULT_LOSE:
            return general_config.EXP_LOSE_RATE
        if result == RESULT_DRAW:
            return general_config.EXP_DRAW_RATE
        return Decimal("0")
