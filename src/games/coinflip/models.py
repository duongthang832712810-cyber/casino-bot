from __future__ import annotations

from dataclasses import dataclass

from src.services.progression_service import ProgressionUpdate


@dataclass(slots=True)
class CoinFlipGame:
    user_id: str
    bet_amount: int
    choice: str
    resolve_at: int
    channel_id: str | None = None
    message_id: str | None = None
    created_at: int = 0
    updated_at: int = 0


@dataclass(frozen=True, slots=True)
class CoinFlipActionResult:
    game: CoinFlipGame
    finished: bool
    is_new: bool = False
    outcome: str | None = None
    result: str | None = None
    payout: int = 0
    net: int = 0
    exp_delta: int = 0
    progression: ProgressionUpdate | None = None
    achievement_message: str | None = None
