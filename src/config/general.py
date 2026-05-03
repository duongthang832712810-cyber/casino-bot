from __future__ import annotations

from decimal import Decimal

DEFAULT_COINS = 1000
DAILY_REWARD = 500
DAILY_COOLDOWN_SECONDS = 86400

LEVEL_BASE_REQUIRED_EXP = 100
LEVEL_REQUIRED_EXP_GROWTH = Decimal("1.1")
EXP_PROGRESS_BAR_WIDTH = 10

EXP_WIN_RATE = Decimal("0.2")
EXP_LOSE_RATE = Decimal("-0.1")
EXP_DRAW_RATE = Decimal("-0.02")
