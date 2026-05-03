from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LotteryState:
    draw_id: int
    status: str
    jackpot_pool: int
    started_at: int
    ends_at: int
    tickets_sold: int = 0
    participants: int = 0
    announcement_channel_id: str | None = None
    announcement_message_id: str | None = None
    last_draw_number: str | None = None
    last_jackpot_winners: int = 0
    last_total_payout: int = 0
    created_at: int = 0
    updated_at: int = 0


@dataclass(slots=True)
class LotteryAnnouncement:
    guild_id: str
    channel_id: str
    message_id: str | None
    created_at: int
    updated_at: int


@dataclass(slots=True)
class LotteryTicket:
    ticket_id: int
    draw_id: int
    user_id: str
    number: str
    quantity: int
    created_at: int
    updated_at: int


@dataclass(frozen=True, slots=True)
class LotteryPurchaseResult:
    state: LotteryState
    numbers: dict[str, int]
    total_quantity: int
    total_cost: int


@dataclass(frozen=True, slots=True)
class LotteryDrawResult:
    old_draw_id: int
    winning_number: str
    tickets_sold: int
    participants: int
    jackpot_winners: int
    total_payout: int
    jackpot_hit: bool
