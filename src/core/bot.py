from __future__ import annotations

import logging

import discord
from discord.ext import commands

from src.config.settings import Settings
from src.db.connection import Database
from src.db.migrations import run_migrations
from src.games.blackjack.service import BlackjackService
from src.games.coinflip.service import CoinFlipService
from src.games.lottery.service import LotteryService
from src.games.sicbo.service import SicboService
from src.repositories.blackjack_repository import BlackjackRepository
from src.repositories.coinflip_repository import CoinFlipRepository
from src.repositories.lottery_repository import LotteryRepository
from src.repositories.sicbo_repository import SicboRepository
from src.repositories.user_repository import UserRepository
from src.services.game_lock_service import GameLockService

LOGGER = logging.getLogger(__name__)


class CasinoBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=settings.command_prefix, intents=intents)
        self.remove_command("help")
        self.settings = settings
        self.db = Database(settings.database_path)
        self.user_repository: UserRepository | None = None
        self.blackjack_repository: BlackjackRepository | None = None
        self.coinflip_repository: CoinFlipRepository | None = None
        self.lottery_repository: LotteryRepository | None = None
        self.sicbo_repository: SicboRepository | None = None
        self.game_locks = GameLockService()
        self.blackjack_service: BlackjackService | None = None
        self.coinflip_service: CoinFlipService | None = None
        self.lottery_service: LotteryService | None = None
        self.sicbo_service: SicboService | None = None

    async def setup_hook(self) -> None:
        await self.db.connect()
        await run_migrations(self.db)

        self.user_repository = UserRepository(self.db)
        self.blackjack_repository = BlackjackRepository(self.db)
        self.coinflip_repository = CoinFlipRepository(self.db)
        self.lottery_repository = LotteryRepository(self.db)
        self.sicbo_repository = SicboRepository(self.db)
        self.blackjack_service = BlackjackService(
            self.db,
            self.user_repository,
            self.blackjack_repository,
            self.game_locks,
            self.settings.default_coins,
        )
        self.coinflip_service = CoinFlipService(
            self.db,
            self.user_repository,
            self.coinflip_repository,
            self.game_locks,
            self.settings.default_coins,
            self,
        )
        self.lottery_service = LotteryService(
            self.db,
            self.user_repository,
            self.lottery_repository,
            self.settings.default_coins,
            self,
        )
        self.sicbo_service = SicboService(
            self.db,
            self.user_repository,
            self.sicbo_repository,
            self.settings.default_coins,
            self,
        )

        await self.load_extension("src.games.blackjack.cog")
        await self.load_extension("src.games.coinflip.cog")
        await self.load_extension("src.games.lottery.cog")
        await self.load_extension("src.games.sicbo.cog")
        await self.load_extension("src.cogs.profile")
        await self.load_extension("src.cogs.economy")
        await self.load_extension("src.cogs.help")

        await self.coinflip_service.recover_pending_games()
        await self.lottery_service.start()
        await self.sicbo_service.start()

        if self.settings.sync_commands:
            await self.tree.sync()
            LOGGER.info("Slash commands synced")

    async def close(self) -> None:
        if self.coinflip_service is not None:
            await self.coinflip_service.close()
        if self.lottery_service is not None:
            await self.lottery_service.close()
        if self.sicbo_service is not None:
            await self.sicbo_service.close()
        await self.db.close()
        await super().close()

    async def on_ready(self) -> None:
        LOGGER.info("Logged in as %s (%s)", self.user, self.user.id if self.user else "unknown")
