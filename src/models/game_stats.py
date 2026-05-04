from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class GameStats:
    user_id: str
    game_type: str
    wins: int
    losses: int
    draws: int
    total_games: int
    current_win_streak: int
    current_loss_streak: int
    best_win_streak: int
    best_loss_streak: int
    total_bet: int
    total_payout: int
    net_profit: int
    biggest_bet: int
    biggest_win: int
    created_at: int
    updated_at: int
