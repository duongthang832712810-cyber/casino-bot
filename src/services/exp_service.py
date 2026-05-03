from __future__ import annotations

from src.services.progression_service import ProgressionService


class ExpService:
    @staticmethod
    def exp_delta_for_result(bet: int, result: str) -> int:
        return ProgressionService.exp_delta_for_result(bet, result)
