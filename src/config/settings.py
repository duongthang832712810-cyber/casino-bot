from __future__ import annotations

import os
from dataclasses import dataclass

from src.config import general as general_config


@dataclass(frozen=True, slots=True)
class Settings:
    discord_token: str
    command_prefix: str = "!"
    database_path: str = "data/bot.sqlite3"
    default_coins: int = general_config.DEFAULT_COINS
    daily_reward: int = general_config.DAILY_REWARD
    daily_cooldown_seconds: int = general_config.DAILY_COOLDOWN_SECONDS
    log_level: str = "INFO"
    sync_commands: bool = True
    owner_id: int | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token:
            raise RuntimeError("Missing DISCORD_TOKEN environment variable")

        owner_id_raw = os.getenv("OWNER_ID", "").strip()
        try:
            owner_id = int(owner_id_raw) if owner_id_raw else None
        except ValueError as exc:
            raise RuntimeError("OWNER_ID must be a Discord user ID number") from exc

        return cls(
            discord_token=token,
            command_prefix=os.getenv("COMMAND_PREFIX", "!"),
            database_path=os.getenv("DATABASE_PATH", "data/bot.sqlite3"),
            default_coins=general_config.DEFAULT_COINS,
            daily_reward=general_config.DAILY_REWARD,
            daily_cooldown_seconds=general_config.DAILY_COOLDOWN_SECONDS,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            sync_commands=os.getenv("SYNC_COMMANDS", "true").lower() in {"1", "true", "yes", "on"},
            owner_id=owner_id,
        )
