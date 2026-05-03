class BotError(Exception):
    """Base application error."""


class NotEnoughCoinsError(BotError):
    pass


class GameNotFoundError(BotError):
    pass


class NotGameOwnerError(BotError):
    pass


class InvalidBetAmountError(BotError):
    pass


class ActiveGameExistsError(BotError):
    pass


class DailyRewardCooldownError(BotError):
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Daily reward is still on cooldown.")


class DatabaseError(BotError):
    pass
