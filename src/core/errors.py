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


class FeatureLockedError(BotError):
    def __init__(self, feature_name: str, required_level: int) -> None:
        self.feature_name = feature_name
        self.required_level = required_level
        super().__init__(f"{feature_name} is locked. Play games to earn EXP and reach Lv.{required_level}.")


class MiningComputerLimitError(BotError):
    pass


class MiningNoComputerError(BotError):
    pass


class MiningClaimCooldownError(BotError):
    def __init__(self, retry_after_seconds: int, message: str) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message)


class MiningNoStoredCoinsError(BotError):
    pass


class DatabaseError(BotError):
    pass
