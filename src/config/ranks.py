from __future__ import annotations

from src.config.emojis import (
    RANK_A_EMOJI,
    RANK_B_EMOJI,
    RANK_C_EMOJI,
    RANK_D_EMOJI,
    RANK_E_EMOJI,
    RANK_F_EMOJI,
    RANK_SSS_EMOJI,
    RANK_SS_EMOJI,
    RANK_S_EMOJI,
)

# Ordered from highest to lowest. Levels above SSS_LEVEL keep SSS rank.
SSS_LEVEL = 150

RANKS = (
    (150, "SSS", RANK_SSS_EMOJI),
    (120, "SS", RANK_SS_EMOJI),
    (90, "S", RANK_S_EMOJI),
    (70, "A", RANK_A_EMOJI),
    (50, "B", RANK_B_EMOJI),
    (35, "C", RANK_C_EMOJI),
    (20, "D", RANK_D_EMOJI),
    (10, "E", RANK_E_EMOJI),
    (0, "F", RANK_F_EMOJI),
)
