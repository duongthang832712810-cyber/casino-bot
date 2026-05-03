from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class User:
    user_id: str
    coins: int
    exp: int
    wins: int
    losses: int
    draws: int
    total_games: int
    has_game: bool
    active_game_type: str | None
    daily_claimed_at: int
    created_at: int
    updated_at: int
