from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from src.config.settings import Settings
from src.db.connection import Database
from src.db.migrations import run_migrations
from src.games.baucua.service import BaucuaService
from src.games.blackjack.service import BlackjackService
from src.games.coinflip.service import CoinFlipService
from src.games.lottery.service import LotteryService
from src.games.sicbo.service import SicboService
from src.repositories.baucua_repository import BaucuaRepository
from src.repositories.blackjack_repository import BlackjackRepository
from src.repositories.achievement_repository import AchievementRepository
from src.repositories.coinflip_repository import CoinFlipRepository
from src.repositories.game_stats_repository import GameStatsRepository
from src.repositories.lottery_repository import LotteryRepository
from src.repositories.sicbo_repository import SicboRepository
from src.repositories.user_repository import UserRepository
from src.services.daily_reward_service import DailyRewardService
from src.services.achievement_service import AchievementService
from src.services.game_lock_service import GameLockService
from src.services.game_stats_service import GameStatsService
from src.services.leaderboard_service import LeaderboardService

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
        self.baucua_repository: BaucuaRepository | None = None
        self.game_stats_repository: GameStatsRepository | None = None
        self.achievement_repository: AchievementRepository | None = None
        self.game_locks = GameLockService()
        self.blackjack_service: BlackjackService | None = None
        self.coinflip_service: CoinFlipService | None = None
        self.lottery_service: LotteryService | None = None
        self.sicbo_service: SicboService | None = None
        self.baucua_service: BaucuaService | None = None
        self.daily_reward_service: DailyRewardService | None = None
        self.achievement_service: AchievementService | None = None
        self.game_stats_service: GameStatsService | None = None
        self.leaderboard_service: LeaderboardService | None = None

    async def setup_hook(self) -> None:
        await self.db.connect()
        await run_migrations(self.db)

        self.user_repository = UserRepository(self.db)
        self.blackjack_repository = BlackjackRepository(self.db)
        self.coinflip_repository = CoinFlipRepository(self.db)
        self.lottery_repository = LotteryRepository(self.db)
        self.sicbo_repository = SicboRepository(self.db)
        self.baucua_repository = BaucuaRepository(self.db)
        self.game_stats_repository = GameStatsRepository(self.db)
        self.achievement_repository = AchievementRepository(self.db)
        self.achievement_service = AchievementService(self.achievement_repository, self.user_repository)
        self.game_stats_service = GameStatsService(self.game_stats_repository, self.user_repository, self.achievement_service)
        self.leaderboard_service = LeaderboardService(self.user_repository, self.game_stats_repository)
        self.blackjack_service = BlackjackService(
            self.db,
            self.user_repository,
            self.blackjack_repository,
            self.game_locks,
            self.settings.default_coins,
            self.game_stats_service,
        )
        self.coinflip_service = CoinFlipService(
            self.db,
            self.user_repository,
            self.coinflip_repository,
            self.game_locks,
            self.settings.default_coins,
            self,
            self.game_stats_service,
        )
        self.lottery_service = LotteryService(
            self.db,
            self.user_repository,
            self.lottery_repository,
            self.settings.default_coins,
            self,
            self.game_stats_service,
        )
        self.sicbo_service = SicboService(
            self.db,
            self.user_repository,
            self.sicbo_repository,
            self.settings.default_coins,
            self,
            self.game_stats_service,
        )
        self.baucua_service = BaucuaService(
            self.db,
            self.user_repository,
            self.baucua_repository,
            self.settings.default_coins,
            self,
            self.game_stats_service,
        )
        self.daily_reward_service = DailyRewardService(
            self.db,
            self.user_repository,
            self.settings.default_coins,
            self.settings.daily_reward,
            self.settings.daily_cooldown_seconds,
        )

        self.tree.on_error = self.on_app_command_error

        await self.load_extension("src.games.blackjack.cog")
        await self.load_extension("src.games.coinflip.cog")
        await self.load_extension("src.games.lottery.cog")
        await self.load_extension("src.games.sicbo.cog")
        await self.load_extension("src.games.baucua.cog")
        await self.load_extension("src.cogs.profile")
        await self.load_extension("src.cogs.leaderboard")
        await self.load_extension("src.cogs.economy")
        await self.load_extension("src.cogs.help")

        await self.coinflip_service.recover_pending_games()
        await self.lottery_service.start()
        await self.sicbo_service.start()
        await self.baucua_service.start()

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
        if self.baucua_service is not None:
            await self.baucua_service.close()
        await self.db.close()
        await super().close()

    async def on_ready(self) -> None:
        LOGGER.info("Logged in as %s (%s)", self.user, self.user.id if self.user else "unknown")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, (commands.MissingPermissions, commands.BotMissingPermissions)):
            await ctx.reply("You do not have permission to use this command.", mention_author=True)
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(f"Missing required argument: `{error.param.name}`.", mention_author=True)
            return
        if isinstance(error, commands.BadArgument):
            await ctx.reply(f"Invalid command argument. Use `{ctx.clean_prefix}help` to view command usage.", mention_author=True)
            return
        if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, Exception):
            LOGGER.error("Unexpected prefix command error", exc_info=_exception_info(error.original))
            await ctx.reply("An unexpected error occurred. Please try again later.", mention_author=True)
            return

        LOGGER.error("Unexpected prefix command error", exc_info=_exception_info(error))
        await ctx.reply("An unexpected error occurred. Please try again later.", mention_author=True)

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            await self._send_interaction_error(interaction, "You do not have permission to use this command.")
            return
        if isinstance(error, app_commands.CommandInvokeError):
            LOGGER.error("Unexpected slash command error", exc_info=_exception_info(error.original))
            await self._send_interaction_error(interaction, "An unexpected error occurred. Please try again later.")
            return

        LOGGER.error("Unexpected slash command error", exc_info=_exception_info(error))
        await self._send_interaction_error(interaction, "An unexpected error occurred. Please try again later.")

    @staticmethod
    async def _send_interaction_error(interaction: discord.Interaction, message: str) -> None:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
            return
        await interaction.response.send_message(message, ephemeral=True)


def _exception_info(exc: BaseException) -> tuple[type[BaseException], BaseException, object]:
    return (type(exc), exc, exc.__traceback__)
