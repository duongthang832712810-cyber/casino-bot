<div align="center">

<pre>
██╗     ██╗   ██╗ ██████╗██╗  ██╗██╗   ██╗██████╗  ██████╗ ██╗  ██╗
██║     ██║   ██║██╔════╝██║ ██╔╝╚██╗ ██╔╝██╔══██╗██╔═══██╗╚██╗██╔╝
██║     ██║   ██║██║     █████╔╝  ╚████╔╝ ██████╔╝██║   ██║ ╚███╔╝ 
██║     ██║   ██║██║     ██╔═██╗   ╚██╔╝  ██╔══██╗██║   ██║ ██╔██╗ 
███████╗╚██████╔╝╚██████╗██║  ██╗   ██║   ██████╔╝╚██████╔╝██╔╝ ██╗
╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝    
</pre>

[![Version](https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge)]()
[![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python&logoColor=white)]()
[![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?style=for-the-badge&logo=discord&logoColor=white)]()
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)]()
[![Tests](https://img.shields.io/badge/tests-pytest-orange?style=for-the-badge&logo=pytest&logoColor=white)]()
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)]()

**A feature-rich Discord casino & economy bot -- virtual coins, real fun.**

[Features](#features) &bull; [Installation](#installation) &bull; [Commands](#commands) &bull; [Progression](#progression-system) &bull; [Config](#configuration) &bull; [Database](#database) &bull; [Development](#development)

</div>

---

> [!IMPORTANT]
> **LuckyBot+ is an entertainment-only project.**
> All coins, tickets, jackpots, EXP, and rewards are **100% virtual** and carry no real-world value whatsoever.
> They cannot be exchanged, sold, withdrawn, or converted into real money, cryptocurrency, gift cards, or any goods or services.
> All casino-style features are purely fictional and exist for fun inside Discord servers only.

---

## Features

<table>
<tr>
<td width="50%">

**Economy & Profile**
- Coin balance system
- Daily reward with cooldown
- Peer-to-peer coin transfers
- Paginated user profiles with game stats
- Current Lottery ticket count in profile
- EXP progress bar with rank emojis

</td>
<td width="50%">

**Progression**
- Level & EXP system
- Win / Lose / Draw EXP rates
- Level-up & level-drop notifications
- Game stats, streaks, and achievements
- Leaderboards for coins, level, wins, profit, bets, and achievements

</td>
</tr>
<tr>
<td width="50%">

**Games**
- Blackjack -- Hit, Stand, Double with buttons
- Coin Flip -- Delayed resolution, edited result
- Lottery -- Multi-tier jackpot pool system
- Sicbo -- Global round-based Big/Small dice game
- Baucua -- Global round-based symbol betting game

</td>
<td width="50%">

**System**
- Slash commands + Prefix commands (mirrored)
- Paginated custom help system with buttons
- Admin channel setup for live game embeds
- Fully atomic database transactions
- Pending game recovery after bot restart

</td>
</tr>
</table>

---

## Project Structure

```
LuckyBot+/
|-- bot.py                        # Main entry point
|-- src/
|   |-- cogs/                     # Discord command & interaction wiring
|   |-- config/
|   |   |-- settings.py           # Environment-based settings
|   |   |-- general.py            # Economy defaults, daily reward, EXP & level config
|   |   |-- emojis.py             # Centralized custom emoji constants
|   |   |-- footer.py             # Random footer message pool
|   |   |-- achievements.py       # Achievement definitions
|   |   |-- leaderboard.py        # Leaderboard config
|   |   |-- ranks.py              # Rank display config
|   |   |-- blackjack.py          # Blackjack bet & payout config
|   |   |-- coinflip.py           # Coin Flip delay & payout config
|   |   |-- lottery.py            # Lottery draw, jackpot & tier config
|   |   |-- sicbo.py              # Sicbo round, bet & display config
|   |   `-- baucua.py             # Baucua round, bet & display config
|   |-- core/                     # Setup, constants, errors, checks, logging
|   |-- db/                       # SQLite connection, schema, migrations
|   |-- games/                    # Game packages
|   |-- repositories/             # Raw SQL data access layer
|   |-- services/                 # Business logic (shared & per-game)
|   `-- utils/                    # Number formatting & utility helpers
`-- tests/                        # pytest unit tests
```

### Architecture

```
+----------+    +----------+    +--------------+    +--------------+    +--------+
|  Config  |--->|   Cogs   |--->|   Services   |--->| Repositories |--->| SQLite |
+----------+    +----------+    +--------------+    +--------------+    +--------+
                                       |
                                       v
                               +---------------+
                               |   Renderers   |
                               |  (embeds only)|
                               +---------------+
```

> Business logic -> `services/` | SQL -> `repositories/` | Embeds -> `renderers/` | Tunable values -> `config/`

---

## Installation

### Requirements

| Requirement | Version |
|:------------|:-------:|
| Python | 3.10+ |
| discord.py | 2.x |
| aiosqlite | latest |

### Steps

**1. Clone the repo & create a virtual environment**

```bash
git clone https://github.com/your-username/luckybot-plus.git
cd luckybot-plus

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure environment**

```bash
cp env.example .env
```

Fill in `.env`:

```env
DISCORD_TOKEN=your_bot_token_here
COMMAND_PREFIX=!
DATABASE_PATH=data/bot.sqlite3
LOG_LEVEL=INFO
SYNC_COMMANDS=true
```

> [!WARNING]
> Never share your `DISCORD_TOKEN`. Treat it like a password.
>
> Economy defaults such as starting coins, daily reward amount, and daily cooldown are configured in `src/config/general.py`, not `.env`.

**4. Run the bot**

```bash
python bot.py
```

---

## Commands

LuckyBot+ supports both **slash commands** (`/`) and **prefix commands** (`!`). Both behave identically.

### Economy

| Command | Description |
|:--------|:------------|
| `/balance` / `/bal` | Check your coin balance |
| `/daily` | Claim your daily coin reward (cooldown applies) |
| `/give @user <amount>` | Transfer coins to another user |

> Transfers are fully atomic. Self-transfers, zero amounts, and insufficient balance are all rejected.

---

### Profile

| Command | Description |
|:--------|:------------|
| `/profile` / `!profile` | View your paginated profile, level, EXP, coins, current Lottery tickets, per-game stats, and achievements |

---

### Blackjack

```
/bj bet <amount>
!bj bet <amount>
```

| Action | Description |
|:-------|:------------|
| Hit | Draw one card |
| Stand | Let the dealer play out |
| Double | Double bet, draw one card, auto-resolve |

- Bet is deducted upfront. Game state is stored in SQLite.
- Double earns double EXP naturally since the bet doubles before result resolution.
- When the game ends, the game row is deleted and active game state is cleared.

---

### Coin Flip

```
/cf bet <h|heads|t|tails> <amount>
!cf bet <h|heads|t|tails> <amount>
```

- Bet is deducted immediately upon starting.
- The flip resolves after a short delay and edits the original message with the result.
- Pending flips survive bot restarts and are recovered automatically.

---

### Lottery

| Command | Description |
|:--------|:------------|
| `/lt buy <number> <qty>` | Buy tickets for a specific number (`0001`-`9999`) |
| `/lt random <qty>` | Buy tickets with randomly assigned numbers |
| `/lt tickets` | View your tickets for the current draw |
| `/lt info` | View draw details and current jackpot pool |
| `/lt set <channel>` | *(Admin)* Set the Lottery announcement channel |
| `!lt buy <number> <qty>` | Prefix ticket purchase command |
| `!lt random <qty>` | Prefix random ticket purchase command |
| `!lt tickets` | Prefix current tickets command |
| `!lt info` | Prefix draw info command |
| `!lt set #channel` | *(Admin)* Prefix announcement channel command |

**Payout tiers** -- only the highest match pays per ticket:

| Match | Payout |
|:------|:-------|
| Last 1 digit | Fixed payout |
| Last 2 digits | Fixed payout |
| Last 3 digits | Fixed payout |
| All 4 digits | [JACKPOT] Split equally among all winners |

> If no one wins the jackpot, the pool carries forward. If the jackpot is hit, the next pool starts from the initial seed plus any split remainder.

---

### Sicbo

```
/sb bet <big|small|tai|xiu> <amount>
```

| Command | Description |
|:--------|:------------|
| `/sb bet <choice> <amount>` | Place your bet for the current round |
| `/sb info` | View current round info and open bets |
| `/sb set <channel>` | *(Admin)* Set the Sicbo announcement channel |
| `!sb bet <choice> <amount>` | Prefix bet command |
| `!sb info` | Prefix current round info command |
| `!sb set #channel` | *(Admin)* Prefix announcement channel command |

**Dice outcome rules:**

| Result | Condition |
|:-------|:----------|
| Small wins | Dice total 4 - 10 |
| Big wins | Dice total 11 - 17 |
| House wins | Dice total 3 or 18 -- both sides lose |

> Sicbo is a global, round-based game. Level-change messages for all players in a round are combined into one message to avoid spam.

---

### Baucua

```
/bc bet <deer|pear|chicken|fish|crab|shrimp> <amount>
```

| Command | Description |
|:--------|:------------|
| `/bc bet <choice> <amount>` | Place your bet for the current round |
| `/bc info` | View current round info and open bets |
| `/bc set <channel>` | *(Admin)* Set the Baucua announcement channel |
| `!bc bet <choice> <amount>` | Prefix bet command |
| `!baucua bet <choice> <amount>` | Prefix alias bet command |

Baucua supports choices: deer, pear, chicken, fish, crab, and shrimp.
Vietnamese aliases are also accepted for common inputs such as nai, bau, ga, ca, cua, and tom.
Each round rolls three symbols.
Each matching symbol pays bet x2.
If a user bets 100 coins on Chicken and one Chicken appears, the displayed payout is +200 coins and the net profit is 100 coins.
If two Chickens appear, the displayed payout is +400 coins and the net profit is 300 coins.
If three Chickens appear, the displayed payout is +600 coins and the net profit is 500 coins.
The Baucua result embed deletes losing bettor names and shows only winning fields with displayed gross payout.

---

### Help

```
/help <page>
```

| Page | Content |
|:----:|:--------|
| 1 | Blackjack |
| 2 | Coin Flip |
| 3 | Lottery |
| 4 | Sicbo |
| 5 | Baucua |

Use the navigation buttons to switch between pages.

---

### Leaderboard

| Command | Description |
|:--------|:------------|
| `/top [category] [game]` | View casino leaderboards |
| `!top [category] [game]` | Prefix leaderboard command |

Categories: `coins`, `level`, `wins`, `profit`, `bet`, `achievements`.
Game filters: `all`, `blackjack`, `coinflip`, `lottery`, `sicbo`, `baucua`.
Coins, level, and achievements are global-only; wins, profit, and bet can be filtered by game.

---

## Progression System

EXP is earned or lost after resolved wager games. Lottery records stats and achievements, but does not grant EXP. EXP amount scales with your bet.

| Result | EXP Rate |
|:-------|:--------:|
| Win | +20% of bet |
| Draw | -2% of bet |
| Lose | -10% of bet |

**Level requirements** grow at x1.1 per level, starting from 100 EXP at Lv.0:

```
Lv.0 ->  100 EXP
Lv.1 ->  110 EXP
Lv.2 ->  121 EXP
Lv.3 ->  133 EXP
...and so on
```

**Rules:**
- EXP resets to the remainder when leveling up
- Dropping levels is possible if EXP goes negative
- You can never fall below Lv.0, and EXP cannot go below 0 at Lv.0
- All EXP values use floor rounding

---

## Configuration

All tunable values live in `src/config/`. Game logic never hardcodes numbers. Starting coins, daily reward amount, and daily cooldown are configured in `src/config/general.py`.

| File | Controls |
|:-----|:---------|
| `general.py` | Default coins, daily reward, daily cooldown, EXP rates, level growth multiplier, progress bar width |
| `achievements.py` | Global and per-game achievement definitions |
| `leaderboard.py` | Leaderboard categories and limits |
| `ranks.py` | Rank thresholds and rank emoji mapping |
| `blackjack.py` | Min/max bet, dealer behavior rules, payout multipliers |
| `coinflip.py` | Min/max bet, resolve delay duration, payout multiplier |
| `lottery.py` | Ticket price, tier payouts, jackpot seed, house edge rate |
| `sicbo.py` | Round duration, min/max bet, payout multiplier |
| `baucua.py` | Round duration, min/max bet, payout multiplier, displayed bettor limit |
| `emojis.py` | All custom emoji IDs -- single source of truth |
| `footer.py` | Random footer message pool for embeds |

---

## Database

Schema is defined in `src/db/schema.sql` and migrated automatically on startup.

| Table | Purpose |
|:------|:--------|
| `users` | Balances, EXP, level, global stats, streaks, active game flag, daily timestamp |
| `blackjack_games` | Active Blackjack game state |
| `coinflip_games` | Pending delayed Coin Flip games |
| `lottery_state` | Current draw state and jackpot pool |
| `lottery_tickets` | Tickets for the current draw (cleared after each draw) |
| `lottery_announcements` | Announcement channel & message ID references |
| `sicbo_state` | Current Sicbo round state |
| `sicbo_bets` | All bets placed in the current round |
| `sicbo_announcements` | Announcement channel & message ID references |
| `baucua_state` | Current Baucua round state |
| `baucua_bets` | All bets placed in the current Baucua round |
| `baucua_announcements` | Announcement channel & message ID references |
| `user_game_stats` | Per-user, per-game wins/losses/draws, streaks, bet, payout, and profit stats |
| `user_achievements` | Unlocked achievements per user |

> [!NOTE]
> All writes involving coins, game state, tickets, jackpots, or active game flags use `immediate_transaction` for full atomicity. Coins are never lost during crashes or concurrent updates.

---

## Testing

```bash
# Compile-check the entire project
python -m compileall bot.py src tests

# Run the test suite
pytest
```

Current coverage: Blackjack payout, Blackjack rules & scoring, Sicbo rules, wallet checks, progression logic.

> Clean up `__pycache__` folders after running `compileall`.

---

## Development

| Rule | Detail |
|:-----|:-------|
| Language | English only -- identifiers, comments, embeds, all user-facing text |
| Game logic | Lives in `services/` only |
| SQL | Lives in `repositories/` only |
| Embeds | Built in `renderers/` only -- no DB writes, no payout calculations |
| Numbers | All tunable values in `config/` only |
| Emojis | All custom emoji IDs in `src/config/emojis.py` -- nowhere else |
| Formatting | Use `format_coin` and `format_number` for all user-facing numbers |
| Sleep | Always `async sleep` -- never blocking sleep |
| Transactions | Atomic whenever coins, game state, tickets, or jackpots are involved |
| Errors | Log unexpected exceptions; always show clean user-facing messages |

---

## License

MIT License -- see [`LICENSE`](./LICENSE) for details.

Contributions welcome -- keep the virtual-only spirit alive!

---

<div align="center">

**LuckyBot+ v1.0.0** &mdash; Built with discord.py

*All coins are virtual. No real money involved. Just good vibes.*

</div>