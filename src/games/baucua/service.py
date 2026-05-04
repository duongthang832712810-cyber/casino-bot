from __future__ import annotations

import asyncio
import logging
import random
import time
from collections import Counter
from contextlib import suppress

import discord

from src.config import baucua as baucua_config
from src.core.constants import GAME_BAUCUA, RESULT_DRAW, RESULT_LOSE, RESULT_WIN
from src.core.errors import ActiveGameExistsError, BotError, InvalidBetAmountError, NotEnoughCoinsError
from src.db.connection import Database
from src.db.transaction import immediate_transaction
from src.games.baucua.constants import CHOICES, STATUS_BETTING
from src.games.baucua.models import BaucuaBetResult, BaucuaResolveResult, BaucuaRoundView, BaucuaState
from src.games.baucua.renderer import render_baucua_embed
from src.games.baucua.rules import normalize_choice
from src.repositories.baucua_repository import BaucuaRepository
from src.repositories.user_repository import UserRepository
from src.services.achievement_service import format_achievement_unlocks
from src.services.exp_service import ExpService
from src.services.game_stats_service import GameStatsService
from src.services.progression_service import ProgressionService, ProgressionUpdate
from src.utils.money import format_coin
from src.utils.notifications import combine_notifications

LOGGER = logging.getLogger(__name__)


class BaucuaChannelNotSetError(BotError):
    pass


class BaucuaBettingClosedError(BotError):
    pass


class BaucuaService:
    def __init__(
        self,
        db: Database,
        users: UserRepository,
        baucua: BaucuaRepository,
        default_coins: int,
        client: discord.Client,
        game_stats: GameStatsService,
    ) -> None:
        self.db = db
        self.users = users
        self.baucua = baucua
        self.default_coins = default_coins
        self.client = client
        self.game_stats = game_stats
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        await self.ensure_state()
        self._task = asyncio.create_task(self._scheduler())

    async def close(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def ensure_state(self) -> BaucuaState:
        state = await self.baucua.get_state()
        if state is not None:
            return state
        now = int(time.time())
        async with immediate_transaction(self.db):
            existing = await self.baucua.get_state()
            if existing is not None:
                return existing
            return await self.baucua.create_state(now, now + baucua_config.ROUND_SECONDS)

    async def get_round_view(self) -> BaucuaRoundView:
        state = await self.ensure_state()
        bets = await self.baucua.list_bets(state.round_id)
        return BaucuaRoundView(state=state, bets=bets)

    async def set_channel(self, guild_id: int, channel: discord.abc.Messageable, channel_id: int) -> None:
        async with self._lock:
            state = await self.ensure_state()
            old_announcement = await self.baucua.get_announcement(str(guild_id))
            if old_announcement is not None:
                await self._delete_round_message(old_announcement.channel_id, old_announcement.message_id)
            bets = await self.baucua.list_bets(state.round_id)
            message = await channel.send(embed=render_baucua_embed(state, bets, self._bot_name()))
            async with immediate_transaction(self.db):
                await self.baucua.upsert_announcement(str(guild_id), str(channel_id), str(message.id))

    async def place_bet(self, guild_id: int, user_id: str, raw_choice: str, amount: int) -> BaucuaBetResult:
        choice = normalize_choice(raw_choice)
        self._validate_bet(amount)
        await self.ensure_state()
        await self.users.get_or_create(user_id, self.default_coins)

        async with self._lock:
            async with immediate_transaction(self.db):
                state = await self.baucua.get_state()
                if state is None:
                    raise RuntimeError("Baucua state disappeared")
                now = int(time.time())
                if state.status != STATUS_BETTING or now >= state.ends_at:
                    raise BaucuaBettingClosedError("Baucua betting is closed. Please wait for the next round.")
                if await self.baucua.get_announcement(str(guild_id)) is None:
                    raise BaucuaChannelNotSetError("Baucua channel is not set for this server.")

                user = await self.users.get_by_id(user_id)
                if user is None:
                    raise RuntimeError("User disappeared")
                if user.has_game and user.active_game_type != GAME_BAUCUA:
                    raise ActiveGameExistsError(f"You already have an active {user.active_game_type or 'other'} game.")
                if user.coins < amount:
                    raise NotEnoughCoinsError("Not enough coins to bet.")

                await self.users.add_coins(user_id, -amount)
                user_bet = await self.baucua.add_bet(state.round_id, user_id, choice, amount)
                await self.users.set_active_game(user_id, GAME_BAUCUA)
                bets = await self.baucua.list_bets(state.round_id)

        await self.update_round_message()
        return BaucuaBetResult(state=state, bets=bets, user_bet=user_bet)

    async def update_round_message(self) -> None:
        state = await self.baucua.get_state()
        if state is None:
            return
        bets = await self.baucua.list_bets(state.round_id)
        announcements = await self.baucua.list_announcements()
        for announcement in announcements:
            try:
                channel = self.client.get_channel(int(announcement.channel_id)) or await self.client.fetch_channel(int(announcement.channel_id))
                if announcement.message_id:
                    message = await channel.fetch_message(int(announcement.message_id))  # type: ignore[attr-defined]
                    await message.edit(embed=render_baucua_embed(state, bets, self._bot_name()))
                    continue
                message = await channel.send(embed=render_baucua_embed(state, bets, self._bot_name()))  # type: ignore[attr-defined]
                async with immediate_transaction(self.db):
                    await self.baucua.update_announcement_message(announcement.guild_id, str(message.id))
            except Exception:
                LOGGER.exception("Failed to update Baucua round message for guild_id=%s", announcement.guild_id)

    async def send_new_round_messages(self) -> None:
        state = await self.baucua.get_state()
        if state is None:
            return
        bets = await self.baucua.list_bets(state.round_id)
        announcements = await self.baucua.list_announcements()
        for announcement in announcements:
            try:
                channel = self.client.get_channel(int(announcement.channel_id)) or await self.client.fetch_channel(int(announcement.channel_id))
                message = await channel.send(embed=render_baucua_embed(state, bets, self._bot_name()))  # type: ignore[attr-defined]
                async with immediate_transaction(self.db):
                    await self.baucua.update_announcement_message(announcement.guild_id, str(message.id))
            except Exception:
                LOGGER.exception("Failed to send new Baucua round message for guild_id=%s", announcement.guild_id)

    async def send_result_round_messages(self) -> None:
        state = await self.baucua.get_state()
        if state is None:
            return
        bets = await self.baucua.list_bets(state.round_id)
        announcements = await self.baucua.list_announcements()
        for announcement in announcements:
            try:
                await self._delete_round_message(announcement.channel_id, announcement.message_id)
                channel = self.client.get_channel(int(announcement.channel_id)) or await self.client.fetch_channel(int(announcement.channel_id))
                message = await channel.send(embed=render_baucua_embed(state, bets, self._bot_name()))  # type: ignore[attr-defined]
                async with immediate_transaction(self.db):
                    await self.baucua.update_announcement_message(announcement.guild_id, str(message.id))
            except Exception:
                LOGGER.exception("Failed to send Baucua result message for guild_id=%s", announcement.guild_id)

    async def _delete_round_message(self, channel_id: str | None, message_id: str | None) -> None:
        if not channel_id or not message_id:
            return
        try:
            channel = self.client.get_channel(int(channel_id)) or await self.client.fetch_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))  # type: ignore[attr-defined]
            await message.delete()
        except Exception as exc:
            LOGGER.warning("Failed to delete old Baucua round message: %s", exc)

    async def _scheduler(self) -> None:
        await self.client.wait_until_ready()
        while not self.client.is_closed():
            try:
                state = await self.ensure_state()
                if state.status == STATUS_BETTING:
                    await self.update_round_message()
                    await asyncio.sleep(max(0, state.ends_at - int(time.time())))
                    await self.resolve_if_due()
                else:
                    await asyncio.sleep(baucua_config.NEXT_ROUND_DELAY_SECONDS)
                    await self.start_next_round()
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.exception("Baucua scheduler failed")
                await asyncio.sleep(10)

    async def resolve_if_due(self) -> BaucuaResolveResult | None:
        async with self._lock:
            state = await self.ensure_state()
            if state.status != STATUS_BETTING or int(time.time()) < state.ends_at:
                return None
            result = await self._resolve_current_round(state)

        await self.send_result_round_messages()
        await self._send_round_notifications(result)
        return result

    async def _resolve_current_round(self, state: BaucuaState) -> BaucuaResolveResult:
        results = tuple(random.choice(CHOICES) for _ in range(3))
        counts = Counter(results)
        progressions: dict[str, ProgressionUpdate] = {}
        achievement_messages: list[str] = []
        total_payout = 0

        async with immediate_transaction(self.db):
            current_state = await self.baucua.get_state()
            if current_state is None:
                raise RuntimeError("Baucua state disappeared")
            if current_state.status != STATUS_BETTING:
                raise BaucuaBettingClosedError("Baucua betting is already closed.")

            bets = await self.baucua.list_bets(current_state.round_id)
            user_totals: dict[str, dict[str, int]] = {}
            for bet in bets:
                hit_count = counts.get(bet.choice, 0)
                payout = bet.amount * baucua_config.PAYOUT_MULTIPLIER * hit_count
                total_payout += payout
                totals = user_totals.setdefault(bet.user_id, {"bet": 0, "payout": 0})
                totals["bet"] += bet.amount
                totals["payout"] += payout

            for user_id, totals in user_totals.items():
                net = totals["payout"] - totals["bet"]
                if net > 0:
                    result = RESULT_WIN
                elif net < 0:
                    result = RESULT_LOSE
                else:
                    result = RESULT_DRAW
                exp_delta = ExpService.exp_delta_for_result(totals["bet"], result)
                progressions[user_id] = await self.users.update_after_result(user_id, totals["bet"], totals["payout"], exp_delta, result)
                stats_result = await self.game_stats.record_result(user_id, GAME_BAUCUA, result, totals["bet"], totals["payout"])
                message = format_achievement_unlocks(user_id, stats_result.achievements)
                if message is not None:
                    achievement_messages.append(message)

            await self.baucua.finish_round(results)  # type: ignore[arg-type]

        return BaucuaResolveResult(
            old_state=state,
            bets=bets,
            results=results,  # type: ignore[arg-type]
            total_payout=total_payout,
            progressions=progressions,
            achievement_messages=achievement_messages,
        )

    async def _send_round_notifications(self, result: BaucuaResolveResult) -> None:
        level_messages = [
            message
            for user_id, progression in result.progressions.items()
            if (message := ProgressionService.level_change_message(user_id, progression)) is not None
        ]
        content = combine_notifications("\n".join(level_messages), "\n".join(result.achievement_messages))
        if content is None:
            return
        announcements = await self.baucua.list_announcements()
        for announcement in announcements:
            try:
                channel = self.client.get_channel(int(announcement.channel_id)) or await self.client.fetch_channel(int(announcement.channel_id))
                await channel.send(content)  # type: ignore[attr-defined]
            except Exception:
                LOGGER.exception("Failed to send Baucua round notifications for guild_id=%s", announcement.guild_id)

    async def start_next_round(self) -> BaucuaState:
        async with self._lock:
            state = await self.ensure_state()
            if state.status == STATUS_BETTING:
                return state
            now = int(time.time())
            async with immediate_transaction(self.db):
                new_state = await self.baucua.start_next_round(now, now + baucua_config.ROUND_SECONDS)
                await self.baucua.delete_old_bets(new_state.round_id)

        await self.send_new_round_messages()
        return new_state

    def _bot_name(self) -> str | None:
        return self.client.user.display_name if self.client.user is not None else None

    @staticmethod
    def _validate_bet(amount: int) -> None:
        if amount < baucua_config.MIN_BET:
            raise InvalidBetAmountError(f"Minimum bet is {format_coin(baucua_config.MIN_BET)}.")
        if baucua_config.MAX_BET is not None and amount > baucua_config.MAX_BET:
            raise InvalidBetAmountError(f"Maximum bet is {format_coin(baucua_config.MAX_BET)}.")
