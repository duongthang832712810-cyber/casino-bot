from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AchievementDefinition:
    achievement_id: str
    name: str
    description: str
    condition: str
    target: int
    game_type: str | None = None


@dataclass(slots=True)
class UserAchievement:
    user_id: str
    achievement_id: str
    game_type: str | None
    unlocked_at: int
