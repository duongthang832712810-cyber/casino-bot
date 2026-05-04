from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class User:
    user_id: str
    coins: int
    exp: int
    level: int
    wins: int
    losses: int
    draws: int
    total_games: int
    has_game: bool
    active_game_type: str | None
    daily_claimed_at: int
    created_at: int
    updated_at: int
    total_bet: int = 0
    total_payout: int = 0
    net_profit: int = 0
    achievements_unlocked: int = 0
    current_win_streak: int = 0
    current_loss_streak: int = 0
    best_win_streak: int = 0
    best_loss_streak: int = 0
