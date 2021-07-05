CREATE TABLE IF NOT EXISTS guild_settings(
    guild_id BIGINT PRIMARY KEY,
    prefix TEXT
);


CREATE TABLE IF NOT EXISTS user_settings(
    user_id BIGINT PRIMARY KEY
);


CREATE TABLE IF NOT EXISTS role_list(
    guild_id BIGINT,
    role_id BIGINT,
    key TEXT,
    value TEXT,
    PRIMARY KEY (guild_id, role_id, key)
);


CREATE TABLE IF NOT EXISTS channel_list(
    guild_id BIGINT,
    channel_id BIGINT,
    key TEXT,
    value TEXT,
    PRIMARY KEY (guild_id, channel_id, key)
);


DO $$ BEGIN
    CREATE TYPE nobility AS ENUM ('Queen', 'Princess', 'Drone');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


CREATE TABLE IF NOT EXISTS bees(
    id TEXT PRIMARY KEY,  -- the bee identifier
    parent_ids TEXT[],  -- the parents of the bees
    owner_id BIGINT,  -- the ID of the user who owns the bee
    name TEXT,  -- the name given to the bee
    nobility nobility NOT NULL DEFAULT 'Drone',  -- the type of bee that this is
    speed INTEGER NOT NULL DEFAULT 0,  -- how often they produce honey
    fertility INTEGER NOT NULL DEFAULT 0,  -- how many drones spawn on their death
    generation INTEGER NOT NULL DEFAULT 0  -- how many generations this bee has been alive for
);
