from __future__ import annotations

from src.config import blackjack as bj_config
from src.core.constants import GAME_BLACKJACK, RESULT_BLACKJACK, RESULT_LOSE
from src.core.errors import ActiveGameExistsError, GameNotFoundError, InvalidBetAmountError, NotEnoughCoinsError
from src.db.connection import Database
from src.db.transaction import immediate_transaction
from src.games.blackjack.deck import deal_initial_game, pop_card
from src.games.blackjack.models import BlackjackActionResult, BlackjackGame
from src.games.blackjack.rules import compare_hands, dealer_play
from src.games.blackjack.scoring import is_blackjack, is_bust
from src.games.common.payout import blackjack_payout
from src.repositories.blackjack_repository import BlackjackRepository
from src.repositories.user_repository import UserRepository
from src.services.exp_service import ExpService
from src.services.game_lock_service import GameLockService
from src.utils.money import format_coin


class BlackjackService:
    def __init__(
        self,
        db: Database,
        users: UserRepository,
        games: BlackjackRepository,
        locks: GameLockService,
        default_coins: int,
    ) -> None:
        self.db = db
        self.users = users
        self.games = games
        self.locks = locks
        self.default_coins = default_coins

    async def start_or_resume(self, user_id: str, bet_amount: int) -> BlackjackActionResult:
        async with self.locks.lock(user_id):
            user = await self.users.get_or_create(user_id, self.default_coins)

            if user.has_game:
                if user.active_game_type == GAME_BLACKJACK:
                    game = await self.games.get_by_user_id(user_id)
                    if game is not None:
                        return BlackjackActionResult(game=game, finished=False, message="resume")
                    await self.users.set_active_game(user_id, None)
                    await self.db.get_connection().commit()
                    user = await self.users.get_by_id(user_id)
                    if user is None:
                        raise RuntimeError("User disappeared")
                else:
                    raise ActiveGameExistsError(f"You already have an active {user.active_game_type or 'other'} game.")

            self._validate_bet(bet_amount)
            if user.coins < bet_amount:
                raise NotEnoughCoinsError("Not enough coins to bet.")

            player_cards, dealer_cards, deck = deal_initial_game()
            game = BlackjackGame(
                user_id=user_id,
                bet_amount=bet_amount,
                player_cards=player_cards,
                dealer_cards=dealer_cards,
                deck=deck,
            )

            async with immediate_transaction(self.db):
                current_user = await self.users.get_by_id(user_id)
                if current_user is None:
                    raise RuntimeError("User disappeared")
                if current_user.coins < bet_amount:
                    raise NotEnoughCoinsError("Not enough coins to bet.")
                await self.users.add_coins(user_id, -bet_amount)
                await self.games.create(game)
                await self.users.set_active_game(user_id, GAME_BLACKJACK)

            if is_blackjack(game.player_cards):
                return await self._finish_game(user_id, RESULT_BLACKJACK, game)

            return BlackjackActionResult(game=game, finished=False)

    async def hit(self, user_id: str) -> BlackjackActionResult:
        async with self.locks.lock(user_id):
            game = await self._require_game(user_id)
            game.player_cards.append(pop_card(game.deck))

            if is_bust(game.player_cards):
                return await self._finish_game(user_id, RESULT_LOSE, game)

            async with immediate_transaction(self.db):
                await self.games.update(game)
            return BlackjackActionResult(game=game, finished=False)

    async def stand(self, user_id: str) -> BlackjackActionResult:
        async with self.locks.lock(user_id):
            game = await self._require_game(user_id)
            dealer_play(game.dealer_cards, game.deck)
            result = compare_hands(game.player_cards, game.dealer_cards)
            return await self._finish_game(user_id, result, game)

    async def double(self, user_id: str) -> BlackjackActionResult:
        async with self.locks.lock(user_id):
            game = await self._require_game(user_id)
            user = await self.users.get_by_id(user_id)
            if user is None:
                raise GameNotFoundError("User not found.")
            if user.coins < game.bet_amount:
                raise NotEnoughCoinsError("Not enough coins to Double.")

            async with immediate_transaction(self.db):
                await self.users.add_coins(user_id, -game.bet_amount)
                game.bet_amount *= 2
                game.player_cards.append(pop_card(game.deck))

                if is_bust(game.player_cards):
                    result = RESULT_LOSE
                else:
                    dealer_play(game.dealer_cards, game.deck)
                    result = compare_hands(game.player_cards, game.dealer_cards)

                payout, _net = blackjack_payout(game.bet_amount, result)
                exp_delta = ExpService.exp_delta_for_result(game.bet_amount, result)
                await self.users.update_after_result(user_id, payout, exp_delta, result)
                await self.games.delete(user_id)

            payout, net = blackjack_payout(game.bet_amount, result)
            exp_delta = ExpService.exp_delta_for_result(game.bet_amount, result)
            return BlackjackActionResult(game=game, finished=True, result=result, payout=payout, net=net, exp_delta=exp_delta)

    async def save_message(self, user_id: str, channel_id: int | None, message_id: int | None) -> None:
        async with immediate_transaction(self.db):
            await self.games.save_message(
                user_id,
                str(channel_id) if channel_id is not None else None,
                str(message_id) if message_id is not None else None,
            )

    async def _finish_game(self, user_id: str, result: str, game: BlackjackGame) -> BlackjackActionResult:
        payout, net = blackjack_payout(game.bet_amount, result)
        exp_delta = ExpService.exp_delta_for_result(game.bet_amount, result)
        async with immediate_transaction(self.db):
            await self.users.update_after_result(user_id, payout, exp_delta, result)
            await self.games.delete(user_id)
        return BlackjackActionResult(game=game, finished=True, result=result, payout=payout, net=net, exp_delta=exp_delta)

    async def _require_game(self, user_id: str) -> BlackjackGame:
        game = await self.games.get_by_user_id(user_id)
        if game is None:
            raise GameNotFoundError("This Blackjack game has already ended.")
        return game

    @staticmethod
    def _validate_bet(amount: int) -> None:
        if amount < bj_config.MIN_BET:
            raise InvalidBetAmountError(f"Minimum bet is {format_coin(bj_config.MIN_BET)}.")
        if bj_config.MAX_BET is not None and amount > bj_config.MAX_BET:
            raise InvalidBetAmountError(f"Maximum bet is {format_coin(bj_config.MAX_BET)}.")
