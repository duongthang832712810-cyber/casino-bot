from __future__ import annotations

import asyncio
import logging
import random
import time
from contextlib import suppress

import discord

from src.config import sicbo as sicbo_config
from src.core.constants import GAME_SICBO, RESULT_LOSE, RESULT_WIN
from src.core.errors import ActiveGameExistsError, BotError, InvalidBetAmountError, NotEnoughCoinsError
from src.db.connection import Database
from src.db.transaction import immediate_transaction
from src.games.sicbo.constants import CHOICE_ALIASES, CHOICE_BIG, CHOICE_SMALL, RESULT_HOUSE, STATUS_BETTING
from src.games.sicbo.models import SicboBetResult, SicboResolveResult, SicboRoundView, SicboState
from src.games.sicbo.renderer import render_sicbo_embed
from src.repositories.sicbo_repository import SicboRepository
from src.repositories.user_repository import UserRepository
from src.utils.money import format_coin

LOGGER = logging.getLogger(__name__)


class SicboChannelNotSetError(BotError):
    pass


class SicboBettingClosedError(BotError):
    pass


class SicboService:
    def __init__(
        self,
        db: Database,
        users: UserRepository,
        sicbo: SicboRepository,
        default_coins: int,
        client: discord.Client,
    ) -> None:
        self.db = db
        self.users = users
        self.sicbo = sicbo
        self.default_coins = default_coins
        self.client = client
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

    async def ensure_state(self) -> SicboState:
        state = await self.sicbo.get_state()
        if state is not None:
            return state
        now = int(time.time())
        async with immediate_transaction(self.db):
            existing = await self.sicbo.get_state()
            if existing is not None:
                return existing
            return await self.sicbo.create_state(now, now + sicbo_config.ROUND_SECONDS)

    async def get_round_view(self) -> SicboRoundView:
        state = await self.ensure_state()
        bets = await self.sicbo.list_bets(state.round_id)
        return SicboRoundView(state=state, bets=bets)

    async def set_channel(self, guild_id: int, channel: discord.abc.Messageable, channel_id: int) -> None:
        async with self._lock:
            state = await self.ensure_state()
            old_announcement = await self.sicbo.get_announcement(str(guild_id))
            if old_announcement is not None:
                await self._delete_round_message(old_announcement.channel_id, old_announcement.message_id)
            bets = await self.sicbo.list_bets(state.round_id)
            message = await channel.send(embed=render_sicbo_embed(state, bets))
            async with immediate_transaction(self.db):
                await self.sicbo.upsert_announcement(str(guild_id), str(channel_id), str(message.id))

    async def place_bet(self, guild_id: int, user_id: str, raw_choice: str, amount: int) -> SicboBetResult:
        choice = self.normalize_choice(raw_choice)
        self._validate_bet(amount)
        await self.ensure_state()
        await self.users.get_or_create(user_id, self.default_coins)

        async with self._lock:
            async with immediate_transaction(self.db):
                state = await self.sicbo.get_state()
                if state is None:
                    raise RuntimeError("Sicbo state disappeared")
                now = int(time.time())
                if state.status != STATUS_BETTING or now >= state.ends_at:
                    raise SicboBettingClosedError("Sicbo betting is closed. Please wait for the next round.")
                if await self.sicbo.get_announcement(str(guild_id)) is None:
                    raise SicboChannelNotSetError("Sicbo channel is not set for this server.")

                user = await self.users.get_by_id(user_id)
                if user is None:
                    raise RuntimeError("User disappeared")

                existing_bet = await self.sicbo.get_user_bet(state.round_id, user_id)
                if existing_bet is not None:
                    raise ActiveGameExistsError("You already placed a bet in this Sicbo round.")

                if user.has_game:
                    if user.active_game_type == GAME_SICBO:
                        await self.users.set_active_game(user_id, None)
                    else:
                        raise ActiveGameExistsError(f"You already have an active {user.active_game_type or 'other'} game.")

                user = await self.users.get_by_id(user_id)
                if user is None:
                    raise RuntimeError("User disappeared")
                if user.coins < amount:
                    raise NotEnoughCoinsError("Not enough coins to bet.")

                await self.users.add_coins(user_id, -amount)
                user_bet = await self.sicbo.add_bet(state.round_id, user_id, choice, amount)
                await self.users.set_active_game(user_id, GAME_SICBO)
                bets = await self.sicbo.list_bets(state.round_id)

        await self.update_round_message()
        return SicboBetResult(state=state, bets=bets, user_bet=user_bet)

    async def update_round_message(self) -> None:
        state = await self.sicbo.get_state()
        if state is None:
            return
        bets = await self.sicbo.list_bets(state.round_id)
        announcements = await self.sicbo.list_announcements()
        for announcement in announcements:
            try:
                channel = self.client.get_channel(int(announcement.channel_id)) or await self.client.fetch_channel(int(announcement.channel_id))
                if announcement.message_id:
                    message = await channel.fetch_message(int(announcement.message_id))  # type: ignore[attr-defined]
                    await message.edit(embed=render_sicbo_embed(state, bets))
                    continue
                message = await channel.send(embed=render_sicbo_embed(state, bets))  # type: ignore[attr-defined]
                async with immediate_transaction(self.db):
                    await self.sicbo.update_announcement_message(announcement.guild_id, str(message.id))
            except Exception:
                LOGGER.exception("Failed to update Sicbo round message for guild_id=%s", announcement.guild_id)

    async def send_new_round_messages(self) -> None:
        state = await self.sicbo.get_state()
        if state is None:
            return
        bets = await self.sicbo.list_bets(state.round_id)
        announcements = await self.sicbo.list_announcements()
        for announcement in announcements:
            try:
                channel = self.client.get_channel(int(announcement.channel_id)) or await self.client.fetch_channel(int(announcement.channel_id))
                message = await channel.send(embed=render_sicbo_embed(state, bets))  # type: ignore[attr-defined]
                async with immediate_transaction(self.db):
                    await self.sicbo.update_announcement_message(announcement.guild_id, str(message.id))
            except Exception:
                LOGGER.exception("Failed to send new Sicbo round message for guild_id=%s", announcement.guild_id)

    async def _delete_round_message(self, channel_id: str | None, message_id: str | None) -> None:
        if not channel_id or not message_id:
            return
        try:
            channel = self.client.get_channel(int(channel_id)) or await self.client.fetch_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))  # type: ignore[attr-defined]
            await message.delete()
        except Exception:
            LOGGER.warning("Failed to delete old Sicbo round message", exc_info=True)

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
                    await asyncio.sleep(sicbo_config.NEXT_ROUND_DELAY_SECONDS)
                    await self.start_next_round()
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.exception("Sicbo scheduler failed")
                await asyncio.sleep(10)

    async def resolve_if_due(self) -> SicboResolveResult | None:
        async with self._lock:
            state = await self.ensure_state()
            if state.status != STATUS_BETTING or int(time.time()) < state.ends_at:
                return None
            result = await self._resolve_current_round(state)

        await self.update_round_message()
        return result

    async def _resolve_current_round(self, state: SicboState) -> SicboResolveResult:
        dice = (random.randint(1, 6), random.randint(1, 6), random.randint(1, 6))
        total = sum(dice)
        outcome = self.result_for_total(total)
        total_payout = 0

        async with immediate_transaction(self.db):
            current_state = await self.sicbo.get_state()
            if current_state is None:
                raise RuntimeError("Sicbo state disappeared")
            if current_state.status != STATUS_BETTING:
                raise SicboBettingClosedError("Sicbo betting is already closed.")

            bets = await self.sicbo.list_bets(current_state.round_id)
            for bet in bets:
                is_win = outcome != RESULT_HOUSE and bet.choice == outcome
                payout = bet.amount * sicbo_config.PAYOUT_MULTIPLIER if is_win else 0
                total_payout += payout
                result = RESULT_WIN if is_win else RESULT_LOSE
                exp_delta = sicbo_config.EXP_WIN if is_win else sicbo_config.EXP_LOSE
                await self.users.update_after_result(bet.user_id, payout, exp_delta, result)

            await self.sicbo.finish_round(outcome, dice)

        return SicboResolveResult(
            old_state=state,
            bets=bets,
            result=outcome,
            dice=dice,
            total=total,
            total_payout=total_payout,
        )

    async def start_next_round(self) -> SicboState:
        async with self._lock:
            state = await self.ensure_state()
            if state.status == STATUS_BETTING:
                return state
            now = int(time.time())
            async with immediate_transaction(self.db):
                new_state = await self.sicbo.start_next_round(now, now + sicbo_config.ROUND_SECONDS)
                await self.sicbo.delete_old_bets(new_state.round_id)

        await self.send_new_round_messages()
        return new_state

    @staticmethod
    def normalize_choice(raw_choice: str) -> str:
        choice = CHOICE_ALIASES.get(raw_choice.lower().strip())
        if choice is None:
            raise InvalidBetAmountError("Choose big/tai or small/xiu.")
        return choice

    @staticmethod
    def result_for_total(total: int) -> str:
        if total in {3, 18}:
            return RESULT_HOUSE
        if 4 <= total <= 10:
            return CHOICE_SMALL
        return CHOICE_BIG

    @staticmethod
    def _validate_bet(amount: int) -> None:
        if amount < sicbo_config.MIN_BET:
            raise InvalidBetAmountError(f"Minimum bet is {format_coin(sicbo_config.MIN_BET)}.")
        if sicbo_config.MAX_BET is not None and amount > sicbo_config.MAX_BET:
            raise InvalidBetAmountError(f"Maximum bet is {format_coin(sicbo_config.MAX_BET)}.")
