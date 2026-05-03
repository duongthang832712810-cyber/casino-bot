from __future__ import annotations

from dataclasses import dataclass


Card = str


@dataclass(slots=True)
class BlackjackGame:
    user_id: str
    bet_amount: int
    player_cards: list[Card]
    dealer_cards: list[Card]
    deck: list[Card]
    channel_id: str | None = None
    message_id: str | None = None
    created_at: int = 0
    updated_at: int = 0


@dataclass(frozen=True, slots=True)
class BlackjackActionResult:
    game: BlackjackGame
    finished: bool
    result: str | None = None
    payout: int = 0
    net: int = 0
    exp_delta: int = 0
    message: str | None = None
