from __future__ import annotations

import asyncio
import logging
import random
import time
from contextlib import suppress

import discord

from src.config import coinflip as cf_config
from src.config.emojis import COINFLIP_HEADS_EMOJI, COINFLIP_TAILS_EMOJI
from src.core.constants import GAME_COINFLIP, RESULT_LOSE, RESULT_WIN
from src.core.errors import ActiveGameExistsError, GameNotFoundError, InvalidBetAmountError, NotEnoughCoinsError
from src.db.connection import Database
from src.db.transaction import immediate_transaction
from src.games.coinflip.constants import CHOICE_HEADS, CHOICE_MAP, CHOICE_TAILS
from src.games.coinflip.models import CoinFlipActionResult, CoinFlipGame
from src.games.coinflip.renderer import render_coinflip_embed
from src.repositories.coinflip_repository import CoinFlipRepository
from src.repositories.user_repository import UserRepository
from src.services.exp_service import ExpService
from src.services.game_lock_service import GameLockService
from src.utils.money import format_coin

LOGGER = logging.getLogger(__name__)


class CoinFlipService:
    def __init__(
        self,
        db: Database,
        users: UserRepository,
        games: CoinFlipRepository,
        locks: GameLockService,
        default_coins: int,
        client: discord.Client,
    ) -> None:
        self.db = db
        self.users = users
        self.games = games
        self.locks = locks
        self.default_coins = default_coins
        self.client = client
        self._tasks: dict[str, asyncio.Task[None]] = {}

    async def start_or_resume(self, user_id: str, raw_choice: str, bet_amount: int) -> CoinFlipActionResult:
        choice = self.normalize_choice(raw_choice)
        async with self.locks.lock(user_id):
            user = await self.users.get_or_create(user_id, self.default_coins)

            if user.has_game:
                if user.active_game_type == GAME_COINFLIP:
                    game = await self.games.get_by_user_id(user_id)
                    if game is not None:
                        return CoinFlipActionResult(game=game, finished=False, is_new=False)
                    await self.users.set_active_game(user_id, None)
                    await self.db.get_connection().commit()
                else:
                    raise ActiveGameExistsError(f"You already have an active {user.active_game_type or 'other'} game.")

            self._validate_bet(bet_amount)
            user = await self.users.get_by_id(user_id)
            if user is None:
                raise RuntimeError("User disappeared")
            if user.coins < bet_amount:
                raise NotEnoughCoinsError("Not enough coins to bet.")

            now = int(time.time())
            delay = random.randint(cf_config.RESOLVE_DELAY_MIN_SECONDS, cf_config.RESOLVE_DELAY_MAX_SECONDS)
            game = CoinFlipGame(
                user_id=user_id,
                bet_amount=bet_amount,
                choice=choice,
                resolve_at=now + delay,
            )

            async with immediate_transaction(self.db):
                current_user = await self.users.get_by_id(user_id)
                if current_user is None:
                    raise RuntimeError("User disappeared")
                if current_user.coins < bet_amount:
                    raise NotEnoughCoinsError("Not enough coins to bet.")
                await self.users.add_coins(user_id, -bet_amount)
                await self.games.create(game)
                await self.users.set_active_game(user_id, GAME_COINFLIP)

            return CoinFlipActionResult(game=game, finished=False, is_new=True)

    async def save_message(self, user_id: str, channel_id: int | None, message_id: int | None) -> None:
        async with immediate_transaction(self.db):
            await self.games.save_message(
                user_id,
                str(channel_id) if channel_id is not None else None,
                str(message_id) if message_id is not None else None,
            )

    def schedule_resolve(self, user_id: str) -> None:
        if user_id in self._tasks and not self._tasks[user_id].done():
            return
        task = asyncio.create_task(self._resolve_later(user_id))
        self._tasks[user_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(user_id, None))

    async def recover_pending_games(self) -> None:
        for game in await self.games.list_pending():
            self.schedule_resolve(game.user_id)

    async def _resolve_later(self, user_id: str) -> None:
        try:
            await self.client.wait_until_ready()
            game = await self.games.get_by_user_id(user_id)
            if game is None:
                return
            sleep_seconds = max(0, game.resolve_at - int(time.time()))
            await asyncio.sleep(sleep_seconds)
            action = await self.resolve(user_id)
            await self._edit_result_message(action)
        except asyncio.CancelledError:
            raise
        except Exception:
            LOGGER.exception("Failed to resolve coinflip for user_id=%s", user_id)

    async def resolve(self, user_id: str) -> CoinFlipActionResult:
        async with self.locks.lock(user_id):
            game = await self.games.get_by_user_id(user_id)
            if game is None:
                raise GameNotFoundError("This Coin Flip has already ended.")

            outcome = random.choice([CHOICE_HEADS, CHOICE_TAILS])
            result = RESULT_WIN if outcome == game.choice else RESULT_LOSE
            payout, net = self._payout(game.bet_amount, result)
            exp_delta = ExpService.exp_delta_for_result(game.bet_amount, result)

            async with immediate_transaction(self.db):
                existing_game = await self.games.get_by_user_id(user_id)
                if existing_game is None:
                    raise GameNotFoundError("This Coin Flip has already ended.")
                await self.users.update_after_result(user_id, payout, exp_delta, result)
                await self.games.delete(user_id)

            return CoinFlipActionResult(
                game=game,
                finished=True,
                is_new=False,
                outcome=outcome,
                result=result,
                payout=payout,
                net=net,
                exp_delta=exp_delta,
            )

    async def _edit_result_message(self, action: CoinFlipActionResult) -> None:
        game = action.game
        if not game.channel_id or not game.message_id:
            return

        try:
            channel = self.client.get_channel(int(game.channel_id)) or await self.client.fetch_channel(int(game.channel_id))
            message = await channel.fetch_message(int(game.message_id))  # type: ignore[attr-defined]
            footer_text = message.embeds[0].footer.text if message.embeds else None
            player = await self.client.fetch_user(int(game.user_id))
            embed = render_coinflip_embed(
                game,
                player,
                finished=True,
                outcome=action.outcome,
                result=action.result,
                net=action.net,
                footer_text=footer_text,
            )
            content = COINFLIP_HEADS_EMOJI if action.outcome == CHOICE_HEADS else COINFLIP_TAILS_EMOJI
            await message.edit(content=content, embed=embed)
        except Exception:
            LOGGER.exception("Failed to edit coinflip result message for user_id=%s", game.user_id)

    async def close(self) -> None:
        for task in list(self._tasks.values()):
            task.cancel()
        for task in list(self._tasks.values()):
            with suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()

    @staticmethod
    def normalize_choice(raw_choice: str) -> str:
        choice = CHOICE_MAP.get(raw_choice.lower().strip())
        if choice is None:
            raise InvalidBetAmountError("Choose h/heads or t/tails.")
        return choice

    @staticmethod
    def _validate_bet(amount: int) -> None:
        if amount < cf_config.MIN_BET:
            raise InvalidBetAmountError(f"Minimum bet is {format_coin(cf_config.MIN_BET)}.")
        if cf_config.MAX_BET is not None and amount > cf_config.MAX_BET:
            raise InvalidBetAmountError(f"Maximum bet is {format_coin(cf_config.MAX_BET)}.")

    @staticmethod
    def _payout(bet: int, result: str) -> tuple[int, int]:
        if result == RESULT_WIN:
            return bet * cf_config.WIN_PAYOUT_MULTIPLIER, bet
        return 0, -bet
