from __future__ import annotations

import asyncio
import logging
import random
import time
from contextlib import suppress
from math import floor

import discord

from src.config import lottery as lottery_config
from src.core.errors import ActiveGameExistsError, BotError, InvalidBetAmountError, NotEnoughCoinsError
from src.db.connection import Database
from src.db.transaction import immediate_transaction
from src.games.lottery.constants import LOTTERY_STATUS_DRAWING, LOTTERY_STATUS_OPEN
from src.games.lottery.models import LotteryDrawResult, LotteryPurchaseResult, LotteryState
from src.games.lottery.renderer import render_announcement_embed, render_draw_result_embed
from src.repositories.lottery_repository import LotteryRepository
from src.repositories.user_repository import UserRepository
from src.utils.money import format_coin, format_number

LOGGER = logging.getLogger(__name__)


class LotteryDrawClosedError(BotError):
    pass


class LotteryService:
    def __init__(
        self,
        db: Database,
        users: UserRepository,
        lottery: LotteryRepository,
        default_coins: int,
        client: discord.Client,
    ) -> None:
        self.db = db
        self.users = users
        self.lottery = lottery
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

    async def ensure_state(self) -> LotteryState:
        state = await self.lottery.get_state()
        if state is not None:
            return state
        now = int(time.time())
        async with immediate_transaction(self.db):
            existing = await self.lottery.get_state()
            if existing is not None:
                return existing
            return await self.lottery.create_state(
                lottery_config.INITIAL_JACKPOT_POOL,
                now,
                now + lottery_config.DRAW_INTERVAL_SECONDS,
            )

    async def buy(self, user_id: str, number: str, quantity: int) -> LotteryPurchaseResult:
        normalized_number = self.normalize_number(number)
        return await self._purchase(user_id, {normalized_number: quantity})

    async def buy_random(self, user_id: str, quantity: int) -> LotteryPurchaseResult:
        self._validate_quantity(quantity)
        numbers: dict[str, int] = {}
        for _ in range(quantity):
            number = f"{random.randint(lottery_config.NUMBER_MIN, lottery_config.NUMBER_MAX):0{lottery_config.NUMBER_DIGITS}d}"
            numbers[number] = numbers.get(number, 0) + 1
        return await self._purchase(user_id, numbers)

    async def _purchase(self, user_id: str, numbers: dict[str, int]) -> LotteryPurchaseResult:
        total_quantity = sum(numbers.values())
        self._validate_quantity(total_quantity)

        await self.ensure_state()
        await self.users.get_or_create(user_id, self.default_coins)

        async with self._lock:
            async with immediate_transaction(self.db):
                state = await self.lottery.get_state()
                if state is None:
                    raise RuntimeError("Lottery state disappeared")
                now = int(time.time())
                if state.status != LOTTERY_STATUS_OPEN or now >= state.ends_at:
                    raise LotteryDrawClosedError("Lottery draw is closing. Please try again in a moment.")

                user = await self.users.get_by_id(user_id)
                if user is None:
                    raise RuntimeError("User disappeared")
                if user.has_game:
                    raise ActiveGameExistsError("You already have an active game. Finish it before buying Lottery tickets.")

                current_quantity = await self.lottery.user_ticket_quantity(state.draw_id, user_id)
                if current_quantity + total_quantity > lottery_config.MAX_TICKETS_PER_USER_PER_DRAW:
                    raise InvalidBetAmountError(
                        f"Maximum {format_number(lottery_config.MAX_TICKETS_PER_USER_PER_DRAW)} tickets per draw."
                    )

                total_cost = lottery_config.TICKET_PRICE * total_quantity
                if user.coins < total_cost:
                    raise NotEnoughCoinsError("Not enough coins to buy Lottery tickets.")

                is_new_participant = not await self.lottery.user_has_ticket(state.draw_id, user_id)
                jackpot_add = floor(total_cost * lottery_config.JACKPOT_CONTRIBUTION_RATE)
                await self.users.add_coins(user_id, -total_cost)
                await self.lottery.add_purchase(state.draw_id, user_id, numbers, jackpot_add, is_new_participant)

            state = await self.lottery.get_state()
            if state is None:
                raise RuntimeError("Lottery state disappeared")

        await self.update_announcement()
        return LotteryPurchaseResult(state=state, numbers=numbers, total_quantity=total_quantity, total_cost=total_cost)

    async def get_state(self) -> LotteryState:
        return await self.ensure_state()

    async def get_user_tickets(self, user_id: str):
        state = await self.ensure_state()
        return state, await self.lottery.list_user_tickets(state.draw_id, user_id)

    async def set_announcement_channel(self, guild_id: int, channel: discord.abc.Messageable, channel_id: int) -> None:
        async with self._lock:
            state = await self.ensure_state()
            old_announcement = await self.lottery.get_announcement(str(guild_id))
            if old_announcement is not None:
                await self._delete_announcement(old_announcement.channel_id, old_announcement.message_id)
            message = await channel.send(embed=render_announcement_embed(state))
            async with immediate_transaction(self.db):
                await self.lottery.upsert_announcement(str(guild_id), str(channel_id), str(message.id))

    async def update_announcement(self) -> None:
        state = await self.lottery.get_state()
        if state is None:
            return
        announcements = await self.lottery.list_announcements()
        for announcement in announcements:
            try:
                channel = self.client.get_channel(int(announcement.channel_id)) or await self.client.fetch_channel(int(announcement.channel_id))
                if announcement.message_id:
                    message = await channel.fetch_message(int(announcement.message_id))  # type: ignore[attr-defined]
                    await message.edit(embed=render_announcement_embed(state))
                    continue
                message = await channel.send(embed=render_announcement_embed(state))  # type: ignore[attr-defined]
                async with immediate_transaction(self.db):
                    await self.lottery.update_announcement_message(announcement.guild_id, str(message.id))
            except Exception:
                LOGGER.exception("Failed to update lottery announcement for guild_id=%s", announcement.guild_id)

    async def _scheduler(self) -> None:
        await self.client.wait_until_ready()
        while not self.client.is_closed():
            try:
                state = await self.ensure_state()
                sleep_seconds = max(0, state.ends_at - int(time.time()))
                await asyncio.sleep(sleep_seconds)
                await self.resolve_if_due()
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.exception("Lottery scheduler failed")
                await asyncio.sleep(10)

    async def resolve_if_due(self) -> LotteryDrawResult | None:
        async with self._lock:
            state = await self.ensure_state()
            if int(time.time()) < state.ends_at or state.status != LOTTERY_STATUS_OPEN:
                return None
            result = await self._resolve_current_draw(state)

        await self._replace_announcement_with_result(result)
        return result

    async def _resolve_current_draw(self, state: LotteryState) -> LotteryDrawResult:
        async with immediate_transaction(self.db):
            current_state = await self.lottery.get_state()
            if current_state is None:
                raise RuntimeError("Lottery state disappeared")
            if current_state.status != LOTTERY_STATUS_OPEN:
                raise LotteryDrawClosedError("Lottery is already drawing.")
            await self.lottery.set_status(LOTTERY_STATUS_DRAWING)

            tickets = await self.lottery.list_tickets(current_state.draw_id)
            winning_number = f"{random.randint(lottery_config.NUMBER_MIN, lottery_config.NUMBER_MAX):0{lottery_config.NUMBER_DIGITS}d}"

            jackpot_winners = 0
            fixed_payouts: dict[str, int] = {}
            jackpot_quantities: dict[str, int] = {}

            for ticket in tickets:
                matched = self._matched_digits(ticket.number, winning_number)
                if matched == 4:
                    jackpot_winners += ticket.quantity
                    jackpot_quantities[ticket.user_id] = jackpot_quantities.get(ticket.user_id, 0) + ticket.quantity
                elif matched > 0:
                    payout = self._fixed_payout(matched) * ticket.quantity
                    fixed_payouts[ticket.user_id] = fixed_payouts.get(ticket.user_id, 0) + payout

            jackpot_hit = jackpot_winners > 0
            total_payout = sum(fixed_payouts.values())
            new_jackpot_pool = current_state.jackpot_pool

            if jackpot_hit:
                per_ticket = current_state.jackpot_pool // jackpot_winners
                remainder = current_state.jackpot_pool % jackpot_winners
                new_jackpot_pool = lottery_config.INITIAL_JACKPOT_POOL + remainder
                for user_id, quantity in jackpot_quantities.items():
                    payout = per_ticket * quantity
                    fixed_payouts[user_id] = fixed_payouts.get(user_id, 0) + payout
                    total_payout += payout

            for user_id, payout in fixed_payouts.items():
                if payout > 0:
                    await self.users.add_coins(user_id, payout)

            now = int(time.time())
            await self.lottery.reset_for_next_draw(
                current_state.draw_id,
                new_jackpot_pool,
                winning_number,
                jackpot_winners,
                total_payout,
                now,
                now + lottery_config.DRAW_INTERVAL_SECONDS,
            )

            return LotteryDrawResult(
                old_draw_id=current_state.draw_id,
                winning_number=winning_number,
                tickets_sold=current_state.tickets_sold,
                participants=current_state.participants,
                jackpot_winners=jackpot_winners,
                total_payout=total_payout,
                jackpot_hit=jackpot_hit,
            )

    async def _replace_announcement_with_result(self, result: LotteryDrawResult) -> None:
        state = await self.lottery.get_state()
        if state is None:
            return
        announcements = await self.lottery.list_announcements()
        for announcement in announcements:
            await self._delete_announcement(announcement.channel_id, announcement.message_id)
            try:
                channel = self.client.get_channel(int(announcement.channel_id)) or await self.client.fetch_channel(int(announcement.channel_id))
                if result.tickets_sold > 0:
                    await channel.send(embed=render_draw_result_embed(result))  # type: ignore[attr-defined]
                message = await channel.send(embed=render_announcement_embed(state))  # type: ignore[attr-defined]
                async with immediate_transaction(self.db):
                    await self.lottery.update_announcement_message(announcement.guild_id, str(message.id))
            except Exception:
                LOGGER.exception("Failed to replace lottery announcement for guild_id=%s", announcement.guild_id)

    async def _delete_announcement(self, channel_id: str | None, message_id: str | None) -> None:
        if not channel_id or not message_id:
            return
        try:
            channel = self.client.get_channel(int(channel_id)) or await self.client.fetch_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))  # type: ignore[attr-defined]
            await message.delete()
        except Exception:
            LOGGER.warning("Failed to delete old lottery announcement", exc_info=True)

    @staticmethod
    def normalize_number(raw_number: str) -> str:
        stripped = raw_number.strip()
        if not stripped.isdigit():
            raise InvalidBetAmountError("Lottery number must be digits only.")
        value = int(stripped)
        if value < lottery_config.NUMBER_MIN or value > lottery_config.NUMBER_MAX:
            raise InvalidBetAmountError("Lottery number must be from 0001 to 9999.")
        return f"{value:0{lottery_config.NUMBER_DIGITS}d}"

    @staticmethod
    def _validate_quantity(quantity: int) -> None:
        if quantity < 1:
            raise InvalidBetAmountError("Quantity must be at least 1.")
        if quantity > lottery_config.MAX_TICKETS_PER_PURCHASE:
            raise InvalidBetAmountError(f"Maximum {format_number(lottery_config.MAX_TICKETS_PER_PURCHASE)} tickets per purchase.")

    @staticmethod
    def _matched_digits(number: str, winning_number: str) -> int:
        if number == winning_number:
            return 4
        if number[-3:] == winning_number[-3:]:
            return 3
        if number[-2:] == winning_number[-2:]:
            return 2
        if number[-1:] == winning_number[-1:]:
            return 1
        return 0

    @staticmethod
    def _fixed_payout(matched_digits: int) -> int:
        ev = 1 - lottery_config.JACKPOT_CONTRIBUTION_RATE - lottery_config.HOUSE_EDGE_RATE
        if matched_digits == 1:
            return floor(lottery_config.TICKET_PRICE * 10 * ev)
        if matched_digits == 2:
            return floor(lottery_config.TICKET_PRICE * 100 * ev)
        if matched_digits == 3:
            return floor(lottery_config.TICKET_PRICE * 1000 * ev)
        return 0
