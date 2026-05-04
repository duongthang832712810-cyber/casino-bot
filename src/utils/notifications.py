from __future__ import annotations


def combine_notifications(*messages: str | None) -> str | None:
    lines = [message for message in messages if message]
    if not lines:
        return None
    return "\n".join(lines)
