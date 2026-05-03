from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GameFinish:
    result: str
    payout: int
    net: int
    exp_delta: int
