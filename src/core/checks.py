from __future__ import annotations


def is_component_owner(interaction_user_id: int, owner_user_id: str) -> bool:
    return str(interaction_user_id) == str(owner_user_id)
