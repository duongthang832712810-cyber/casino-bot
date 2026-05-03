from __future__ import annotations

from src.core.constants import GAME_BLACKJACK
from src.models.user import User
from src.repositories.blackjack_repository import BlackjackRepository
from src.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, users: UserRepository, blackjack_games: BlackjackRepository, default_coins: int) -> None:
        self.users = users
        self.blackjack_games = blackjack_games
        self.default_coins = default_coins

    async def get_or_create(self, user_id: str) -> User:
        return await self.users.get_or_create(user_id, self.default_coins)

    async def repair_blackjack_state_if_needed(self, user: User) -> User:
        if user.has_game and user.active_game_type == GAME_BLACKJACK:
            game = await self.blackjack_games.get_by_user_id(user.user_id)
            if game is None:
                await self.users.set_active_game(user.user_id, None)
                repaired = await self.users.get_by_id(user.user_id)
                if repaired is not None:
                    return repaired
        return user
