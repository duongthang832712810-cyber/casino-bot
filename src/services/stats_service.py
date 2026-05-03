from __future__ import annotations


class StatsService:
    @staticmethod
    def normalize_result_for_stats(result: str) -> str:
        return "win" if result == "blackjack" else result
