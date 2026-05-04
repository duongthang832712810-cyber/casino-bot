from __future__ import annotations

GAME_NAME = "Lucky Mining"

TIER_MIN = 1
TIER_MAX = 7
MAX_COMPUTERS_PER_USER = 6
MAX_ACCUMULATION_SECONDS = 7200
CLAIM_COOLDOWN_SECONDS = 300
PRICE_MULTIPLIER_PER_OWNED_COMPUTER = 1.5
SECONDS_PER_DAY = 86400

TIER_CONFIGS = {
    1: {"base_price": 25000, "daily_income": 1440},
    2: {"base_price": 75000, "daily_income": 3588},
    3: {"base_price": 200000, "daily_income": 7980},
    4: {"base_price": 500000, "daily_income": 16280},
    5: {"base_price": 1200000, "daily_income": 33120},
    6: {"base_price": 3000000, "daily_income": 66500},
    7: {"base_price": 8000000, "daily_income": 136500},
}
