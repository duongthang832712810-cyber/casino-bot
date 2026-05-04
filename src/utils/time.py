from __future__ import annotations

import time


def utc_timestamp() -> int:
    return int(time.time())


def format_duration(seconds: int) -> str:
    seconds = max(0, seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, remaining_seconds = divmod(remainder, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours:,}h")
    if minutes:
        parts.append(f"{minutes:,}m")
    if remaining_seconds or not parts:
        parts.append(f"{remaining_seconds:,}s")
    return " ".join(parts)
