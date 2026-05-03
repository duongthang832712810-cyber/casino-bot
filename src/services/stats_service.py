from __future__ import annotations

from src.core.constants import RESULT_BLACKJACK, RESULT_WIN


class StatsService:
    @staticmethod
    def normalize_result_for_stats(result: str) -> str:
        return RESULT_WIN if result == RESULT_BLACKJACK else result
