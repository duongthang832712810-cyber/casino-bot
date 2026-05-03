from __future__ import annotations

from dataclasses import dataclass

from src.services.progression_service import ProgressionUpdate


@dataclass(slots=True)
class SicboState:
    round_id: int
    status: str
    started_at: int
    ends_at: int
    channel_id: str | None = None
    message_id: str | None = None
    result: str | None = None
    dice_1: int | None = None
    dice_2: int | None = None
    dice_3: int | None = None
    created_at: int = 0
    updated_at: int = 0


@dataclass(slots=True)
class SicboAnnouncement:
    guild_id: str
    channel_id: str
    message_id: str | None
    created_at: int
    updated_at: int


@dataclass(slots=True)
class SicboBet:
    bet_id: int
    round_id: int
    user_id: str
    choice: str
    amount: int
    created_at: int
    updated_at: int


@dataclass(frozen=True, slots=True)
class SicboRoundView:
    state: SicboState
    bets: list[SicboBet]


@dataclass(frozen=True, slots=True)
class SicboBetResult:
    state: SicboState
    bets: list[SicboBet]
    user_bet: SicboBet


@dataclass(frozen=True, slots=True)
class SicboResolveResult:
    old_state: SicboState
    bets: list[SicboBet]
    result: str
    dice: tuple[int, int, int]
    total: int
    total_payout: int
    progressions: dict[str, ProgressionUpdate]
