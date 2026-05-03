from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    discord_token: str
    command_prefix: str = "!"
    database_path: str = "data/bot.sqlite3"
    default_coins: int = 1000
    daily_reward: int = 500
    daily_cooldown_seconds: int = 86400
    log_level: str = "INFO"
    sync_commands: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token:
            raise RuntimeError("Missing DISCORD_TOKEN environment variable")

        return cls(
            discord_token=token,
            command_prefix=os.getenv("COMMAND_PREFIX", "!"),
            database_path=os.getenv("DATABASE_PATH", "data/bot.sqlite3"),
            default_coins=int(os.getenv("DEFAULT_COINS", "1000")),
            daily_reward=int(os.getenv("DAILY_REWARD", "500")),
            daily_cooldown_seconds=int(os.getenv("DAILY_COOLDOWN_SECONDS", "86400")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            sync_commands=os.getenv("SYNC_COMMANDS", "true").lower() in {"1", "true", "yes", "on"},
        )
