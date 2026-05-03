# LuckyBot+

LuckyBot+ is a Discord casino and economy bot built with `discord.py` and SQLite. It uses virtual coins only and does not involve real money.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `env.example` to `.env` and fill in your real values.
4. Run the bot:

```bash
python bot.py
```

## Environment

```env
DISCORD_TOKEN=your_bot_token_here
COMMAND_PREFIX=!
DATABASE_PATH=data/bot.sqlite3
LOG_LEVEL=INFO
SYNC_COMMANDS=true
DEFAULT_COINS=1000
DAILY_REWARD=500
DAILY_COOLDOWN_SECONDS=86400
```

## Slash Commands

```text
/help
/balance
/bal
/daily
/profile
/bj amount
/cf choice amount
/lt buy number quantity
/lt random quantity
/lt tickets
/lt info
/lt set-channel channel
/sb choice amount
/sb-info
/sb-set-channel channel
```

## Prefix Commands

```text
!help
!balance
!bal
!daily
!profile
!bj amount
!cf choice amount
!lt
!lt buy number quantity
!lt random quantity
!lt tickets
!lt info
!lt set-channel #channel
!lottery
!lottery buy number quantity
!lottery random quantity
!lottery tickets
!lottery info
!lottery set-channel #channel
!sb choice amount
!sb info
!sb set-channel #channel
!sicbo choice amount
!sicbo info
!sicbo set-channel #channel
```

## Notes

- `/sb choice amount` and `!sb choice amount` place Sicbo bets directly; there is no `bet` subcommand.
- `/sb-info` and `/sb-set-channel` are top-level slash commands because Discord slash commands cannot be both a direct command and a command group at the same time.
- `!lt` and `!sb` without arguments show current Lottery/Sicbo information.
- `.env`, SQLite databases, logs, and virtual environments are ignored by Git.
