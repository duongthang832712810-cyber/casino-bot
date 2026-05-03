from __future__ import annotations

from src.core.errors import NotEnoughCoinsError
from src.models.user import User


class WalletService:
    @staticmethod
    def ensure_can_pay(user: User, amount: int) -> None:
        if user.coins < amount:
            raise NotEnoughCoinsError("Not enough coins")

    @staticmethod
    def clamp_coin(value: int) -> int:
        return max(0, value)
