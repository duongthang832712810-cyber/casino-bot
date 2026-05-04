from __future__ import annotations

from src.core.constants import GAME_BAUCUA, GAME_BLACKJACK, GAME_COINFLIP, GAME_LOTTERY, GAME_SICBO
from src.models.achievement import AchievementDefinition

GAME_TYPES = (GAME_BLACKJACK, GAME_COINFLIP, GAME_LOTTERY, GAME_SICBO, GAME_BAUCUA)
GAME_NAMES = {
    GAME_BLACKJACK: "Blackjack",
    GAME_COINFLIP: "Coin Flip",
    GAME_LOTTERY: "Lottery",
    GAME_SICBO: "Sicbo",
    GAME_BAUCUA: "Baucua",
}

GLOBAL_ACHIEVEMENTS = (
    AchievementDefinition("global_first_win", "First Win", "Win any game once.", "wins", 1),
    AchievementDefinition("global_100_wins", "Century Winner", "Win 100 games total.", "wins", 100),
    AchievementDefinition("global_100_games", "Regular Player", "Play 100 games total.", "total_games", 100),
    AchievementDefinition("global_10_loss_streak", "Cold Streak", "Lose 10 games in a row.", "current_loss_streak", 10),
    AchievementDefinition("global_bet_100000", "Big Better", "Bet 100,000 coins total.", "total_bet", 100000),
    AchievementDefinition("global_profit_100000", "High Roller", "Earn 100,000 net profit total.", "net_profit", 100000),
    AchievementDefinition("global_level_10", "Level 10", "Reach level 10.", "level", 10),
    AchievementDefinition("global_millionaire", "Millionaire", "Hold 1,000,000 coins.", "coins", 1000000),
)

PER_GAME_ACHIEVEMENTS: tuple[AchievementDefinition, ...] = tuple(
    achievement
    for game_type, game_name in GAME_NAMES.items()
    for achievement in (
        AchievementDefinition(f"{game_type}_first_win", f"{game_name} First Win", f"Win {game_name} once.", "wins", 1, game_type),
        AchievementDefinition(f"{game_type}_10_wins", f"{game_name} Winner", f"Win {game_name} 10 times.", "wins", 10, game_type),
        AchievementDefinition(f"{game_type}_100_wins", f"{game_name} Veteran", f"Win {game_name} 100 times.", "wins", 100, game_type),
        AchievementDefinition(f"{game_type}_10_games", f"{game_name} Regular", f"Play {game_name} 10 times.", "total_games", 10, game_type),
        AchievementDefinition(f"{game_type}_100_games", f"{game_name} Grinder", f"Play {game_name} 100 times.", "total_games", 100, game_type),
        AchievementDefinition(f"{game_type}_5_win_streak", f"{game_name} Hot Streak", f"Win 5 {game_name} games in a row.", "current_win_streak", 5, game_type),
        AchievementDefinition(f"{game_type}_10_loss_streak", f"{game_name} Cold Streak", f"Lose 10 {game_name} games in a row.", "current_loss_streak", 10, game_type),
        AchievementDefinition(f"{game_type}_bet_50000", f"{game_name} Better", f"Bet 50,000 coins in {game_name}.", "total_bet", 50000, game_type),
        AchievementDefinition(f"{game_type}_profit_50000", f"{game_name} Profit", f"Earn 50,000 net profit in {game_name}.", "net_profit", 50000, game_type),
    )
)

ACHIEVEMENTS = {achievement.achievement_id: achievement for achievement in (*GLOBAL_ACHIEVEMENTS, *PER_GAME_ACHIEVEMENTS)}
