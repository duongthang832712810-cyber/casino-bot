import pytest

from src.core.errors import NotEnoughCoinsError
from src.models.user import User
from src.services.wallet_service import WalletService


def test_ensure_can_pay():
    user = User("1", 100, 0, 0, 0, 0, 0, False, None, 0, 0, 0)
    WalletService.ensure_can_pay(user, 100)


def test_ensure_can_pay_raises():
    user = User("1", 99, 0, 0, 0, 0, 0, False, None, 0, 0, 0)
    with pytest.raises(NotEnoughCoinsError):
        WalletService.ensure_can_pay(user, 100)
