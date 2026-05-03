CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    coins INTEGER NOT NULL DEFAULT 0 CHECK (coins >= 0),
    exp INTEGER NOT NULL DEFAULT 0 CHECK (exp >= 0),

    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    draws INTEGER NOT NULL DEFAULT 0,
    total_games INTEGER NOT NULL DEFAULT 0,

    has_game INTEGER NOT NULL DEFAULT 0,
    active_game_type TEXT,
    daily_claimed_at INTEGER NOT NULL DEFAULT 0,

    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_active_game_type ON users(active_game_type);

CREATE TABLE IF NOT EXISTS blackjack_games (
    user_id TEXT PRIMARY KEY,
    bet_amount INTEGER NOT NULL CHECK (bet_amount > 0),

    player_cards TEXT NOT NULL,
    dealer_cards TEXT NOT NULL,
    deck TEXT NOT NULL,

    channel_id TEXT,
    message_id TEXT,

    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,

    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_blackjack_games_user_id ON blackjack_games(user_id);

CREATE TABLE IF NOT EXISTS coinflip_games (
    user_id TEXT PRIMARY KEY,

    bet_amount INTEGER NOT NULL CHECK (bet_amount > 0),
    choice TEXT NOT NULL,
    resolve_at INTEGER NOT NULL,

    channel_id TEXT,
    message_id TEXT,

    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,

    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_coinflip_games_user_id ON coinflip_games(user_id);
CREATE INDEX IF NOT EXISTS idx_coinflip_games_resolve_at ON coinflip_games(resolve_at);

CREATE TABLE IF NOT EXISTS lottery_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),

    draw_id INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'open',
    jackpot_pool INTEGER NOT NULL,

    started_at INTEGER NOT NULL,
    ends_at INTEGER NOT NULL,

    tickets_sold INTEGER NOT NULL DEFAULT 0,
    participants INTEGER NOT NULL DEFAULT 0,

    announcement_channel_id TEXT,
    announcement_message_id TEXT,

    last_draw_number TEXT,
    last_jackpot_winners INTEGER NOT NULL DEFAULT 0,
    last_total_payout INTEGER NOT NULL DEFAULT 0,

    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS lottery_tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,

    draw_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    number TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,

    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lottery_tickets_draw_id ON lottery_tickets(draw_id);
CREATE INDEX IF NOT EXISTS idx_lottery_tickets_user_id ON lottery_tickets(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_lottery_tickets_draw_user_number ON lottery_tickets(draw_id, user_id, number);

CREATE TABLE IF NOT EXISTS lottery_announcements (
    guild_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    message_id TEXT,

    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lottery_announcements_channel_id ON lottery_announcements(channel_id);

CREATE TABLE IF NOT EXISTS sicbo_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),

    round_id INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'betting',

    started_at INTEGER NOT NULL,
    ends_at INTEGER NOT NULL,

    channel_id TEXT,
    message_id TEXT,

    result TEXT,
    dice_1 INTEGER,
    dice_2 INTEGER,
    dice_3 INTEGER,

    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sicbo_bets (
    bet_id INTEGER PRIMARY KEY AUTOINCREMENT,

    round_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    choice TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),

    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,

    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_sicbo_bets_round_id ON sicbo_bets(round_id);
CREATE INDEX IF NOT EXISTS idx_sicbo_bets_user_id ON sicbo_bets(user_id);
CREATE INDEX IF NOT EXISTS idx_sicbo_bets_round_choice ON sicbo_bets(round_id, choice);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sicbo_bets_round_user ON sicbo_bets(round_id, user_id);

CREATE TABLE IF NOT EXISTS sicbo_announcements (
    guild_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    message_id TEXT,

    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sicbo_announcements_channel_id ON sicbo_announcements(channel_id);
