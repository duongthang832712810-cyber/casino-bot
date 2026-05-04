from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MiningComputer:
    computer_id: int
    user_id: str
    tier: int
    purchase_price: int
    purchased_at: int
    last_claimed_at: int
    created_at: int
    updated_at: int


@dataclass(frozen=True, slots=True)
class MiningStats:
    user_id: str
    total_claimed: int
    computers_bought: int
    highest_tier: int
    last_claimed_at: int
    created_at: int
    updated_at: int


@dataclass(frozen=True, slots=True)
class MiningShopTier:
    tier: int
    base_price: int
    next_price: int
    daily_income: int
    storage_income: int
    owned: int


@dataclass(frozen=True, slots=True)
class MiningPurchaseResult:
    tier: int
    price: int
    total_computers: int


@dataclass(frozen=True, slots=True)
class MiningClaimResult:
    claimed: int
    computer_count: int
    next_claim_at: int


@dataclass(frozen=True, slots=True)
class MiningComputerSummary:
    tier: int
    count: int
    daily_income: int
    stored_income: int
    stored_seconds: int
    remaining_storage_seconds: int
