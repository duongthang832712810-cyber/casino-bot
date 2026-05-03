from __future__ import annotations

import asyncio

from dotenv import load_dotenv

from src.config.settings import Settings
from src.core.bot import CasinoBot
from src.core.logging import setup_logging


async def main() -> None:
    load_dotenv()
    settings = Settings.from_env()
    setup_logging(settings.log_level)

    bot = CasinoBot(settings)
    async with bot:
        await bot.start(settings.discord_token)


if __name__ == "__main__":
    asyncio.run(main())
