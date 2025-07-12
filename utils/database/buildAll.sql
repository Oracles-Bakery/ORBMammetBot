-- The bot's reference index for any channels or messages it tracks
CREATE TABLE IF NOT EXISTS consistentChannels (
    id SERIAL, -- UID
    purpose TEXT UNIQUE NOT NULL,  -- e.g., 'general', 'announcements', etc.
    channel_id BIGINT NOT NULL, -- Channel the message is in
    message_id BIGINT PRIMARY KEY, -- Message pertaining to the function
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Discord roles storage and the accompanying information
CREATE TABLE IF NOT EXISTS discord_roles (
    id SERIAL, -- UID
    role_id BIGINT PRIMARY KEY, -- Discord role ID
    role_name TEXT NOT NULL, -- Name of the role
    category TEXT,  -- e.g., 'FF Role', 'FC Rank', 'Interests', etc.
    emoji_id BIGINT, -- ID of the application emoji
    unicode_emoji TEXT,  -- For custom emojis
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bot heartbeat tracking
CREATE TABLE IF NOT EXISTS bot_status (
    id SERIAL PRIMARY KEY, -- UID
    status TEXT NOT NULL, -- Status message of the bot
    last_heartbeat TIMESTAMP WITH TIME ZONE NOT NULL, -- date of the heartbeat
    reason TEXT -- Optional text for alerting V to a bad crash
);

-- Create the primary database for a user's information
CREATE TABLE IF NOT EXISTS user_data (
    id SERIAL, -- UID
    discord_id BIGINT PRIMARY KEY, -- Main key for almost all relations
    join_date DATE, -- date they joined the discord
    discord_name TEXT NOT NULL, -- Name on discord at time of entry
    preferred_name TEXT NOT NULL, -- Bot can address people how they want to be addressed this way
    steam_id BIGINT, -- Steam ID for later, feels useful u kno
    created_at TIMESTAMP WITH TIME ZONE  DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Warnings and moderation notes
CREATE TABLE IF NOT EXISTS user_warnings (
    id SERIAL, -- UID
    user_warned BIGINT, -- Discord id of warned user
    warned_by BIGINT, -- Discord id of warning issuer
    warning_id BIGSERIAL PRIMARY KEY, -- Big UID to keep things from ever overlapping
    warning_date DATE DEFAULT CURRENT_TIMESTAMP, -- Time issued
    warning_title TEXT NOT NULL, -- Warning title
    warning_reason TEXT NOT NULL, -- Full warning text
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_warned) REFERENCES user_data (discord_id) ON DELETE CASCADE -- Links warnings to the user
);

-- Core character data
CREATE TABLE IF NOT EXISTS xiv_char (
    id SERIAL, -- UID
    lodestone_id BIGINT PRIMARY KEY, -- Lodestone member number
    discord_id BIGINT, -- Discord ID
    forename TEXT, -- Character's forename
    surname TEXT, -- Character's surname
    server_name TEXT, -- Server character resides on
    data_center_name TEXT, -- Data center? Centre? I can never remember.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (discord_id) REFERENCES user_data (discord_id) ON DELETE CASCADE
);

-- Character job levels and progression
CREATE TABLE IF NOT EXISTS xiv_jobs (
    id SERIAL, -- UID
    job_name TEXT PRIMARY KEY, -- 'PLD', 'WHM', etc.
    full_name TEXT NOT NULL, -- 'Paladin', 'White Mage', etc.
    job_role TEXT NOT NULL, -- 'Tank', 'Barrier', 'Magic', 'Limited', 'Gatherer', 'Phantom' etc
    category TEXT NOT NULL, -- 'DoW', 'DoM', 'DoH', 'DoL'
    version_added TEXT NOT NULL, -- e.g., '2.0', '3.0', etc.
    sort_order INTEGER DEFAULT 0, -- Makes list human readable,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Dynamic character ranks
CREATE TABLE IF NOT EXISTS xiv_char_field_ops (
    id SERIAL, -- UID
    lodestone_id BIGINT, -- Lodestone user number
    rank_type TEXT, -- e.g., 'EUREKA', 'BOZJA', etc.
    rank_value INTEGER , -- Level
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (lodestone_id, rank_type),
    FOREIGN KEY (lodestone_id) REFERENCES xiv_char (lodestone_id) ON DELETE CASCADE
);

-- Dynamic character job levels
CREATE TABLE IF NOT EXISTS xiv_char_jobs (
    id SERIAL, -- UID
    lodestone_id BIGINT, -- Lodestone character number
    job_name TEXT,  -- 'GLD', 'PLD', etc.
    job_level INTEGER, -- Level
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (lodestone_id, job_name),
    FOREIGN KEY (lodestone_id) REFERENCES xiv_char (lodestone_id) ON DELETE CASCADE
);

-- Crafting tome progression
CREATE TABLE IF NOT EXISTS xiv_char_crafting (
    id SERIAL, -- UID
    lodestone_id BIGINT, -- Lodestone character number
    craft_type TEXT,  -- e.g., 'CRPDMATERIA', 'BSMMSTRBK01', etc.
    craft_value INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (lodestone_id, craft_type),
    FOREIGN KEY (lodestone_id) REFERENCES xiv_char (lodestone_id) ON DELETE CASCADE
);

-- Community events and activities
CREATE TABLE IF NOT EXISTS xiv_community_events (
    id SERIAL, -- UID
    event_name TEXT UNIQUE NOT NULL,  -- e.g., 'Hunt', 'Treasure Map', etc.
    event_description TEXT, -- Event description for embeds etc
    event_date DATE, -- Date event starts
    event_time TIME, -- Time event starts
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Discord donated keys
CREATE TABLE IF NOT EXISTS discord_donated_keys (
    id BIGSERIAL PRIMARY KEY, -- Big UID just in case
    encrypted_code TEXT NOT NULL, -- Game code (enrypted)
    encrypted_password TEXT NOT NULL, -- Password to unlock (encrypted)
    created_by BIGINT, -- discord user ID
    redeemed_by BIGINT, -- discord user ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    redeemed_at TIMESTAMP
);
