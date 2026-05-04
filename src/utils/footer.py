from __future__ import annotations

import random

from src.config.footer import RANDOM_FOOTER_MESSAGES


def random_footer_text(bot_name: str | None = None) -> str:
    name = bot_name or "LuckyBot+"
    return f"{name} | {random.choice(RANDOM_FOOTER_MESSAGES)}"
