from __future__ import annotations

from dataclasses import dataclass

from src.config.ranks import RANKS


@dataclass(frozen=True, slots=True)
class RankInfo:
    name: str
    emoji: str
    min_level: int


def rank_for_level(level: int) -> RankInfo:
    safe_level = max(0, level)
    for min_level, name, emoji in RANKS:
        if safe_level >= min_level:
            return RankInfo(name=name, emoji=emoji, min_level=min_level)
    min_level, name, emoji = RANKS[-1]
    return RankInfo(name=name, emoji=emoji, min_level=min_level)


def format_ranked_level(level: int) -> str:
    rank = rank_for_level(level)
    return f"{rank.emoji} Lv.{level}"
