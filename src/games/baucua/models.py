from __future__ import annotations

from dataclasses import dataclass

from src.services.progression_service import ProgressionUpdate


@dataclass(slots=True)
class BaucuaState:
    round_id: int
    status: str
    started_at: int
    ends_at: int
    channel_id: str | None = None
    message_id: str | None = None
    result_1: str | None = None
    result_2: str | None = None
    result_3: str | None = None
    created_at: int = 0
    updated_at: int = 0


@dataclass(slots=True)
class BaucuaAnnouncement:
    guild_id: str
    channel_id: str
    message_id: str | None
    created_at: int
    updated_at: int


@dataclass(slots=True)
class BaucuaBet:
    bet_id: int
    round_id: int
    user_id: str
    choice: str
    amount: int
    created_at: int
    updated_at: int


@dataclass(frozen=True, slots=True)
class BaucuaRoundView:
    state: BaucuaState
    bets: list[BaucuaBet]


@dataclass(frozen=True, slots=True)
class BaucuaBetResult:
    state: BaucuaState
    bets: list[BaucuaBet]
    user_bet: BaucuaBet


@dataclass(frozen=True, slots=True)
class BaucuaResolveResult:
    old_state: BaucuaState
    bets: list[BaucuaBet]
    results: tuple[str, str, str]
    total_payout: int
    progressions: dict[str, ProgressionUpdate]
    achievement_messages: list[str]
