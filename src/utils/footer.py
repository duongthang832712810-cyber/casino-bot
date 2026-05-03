from __future__ import annotations

import random

from src.config.footer import RANDOM_FOOTER_MESSAGES


def random_footer_text() -> str:
    return random.choice(RANDOM_FOOTER_MESSAGES)
