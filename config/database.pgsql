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


CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pgcrypto;


DO $$ BEGIN
    CREATE TYPE nobility AS ENUM ('Queen', 'Princess', 'Drone');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


CREATE TABLE IF NOT EXISTS hives(
    id TEXT PRIMARY KEY,
    index SMALLINT,
    guild_id BIGINT,
    owner_id BIGINT,
)


CREATE TABLE IF NOT EXISTS bees(
    id TEXT PRIMARY KEY,  -- the bee identifier
    parent_ids TEXT[],  -- the parents of the bees
    guild_id BIGINT,  -- the ID of the guild that the bee belongs to
    owner_id BIGINT,  -- the ID of the user who owns the bee
    hive_id TEXT REFERENCES hives(id),  -- the ID of the hive that the bee lives in
    name CITEXT,  -- the name given to the bee
    type TEXT NOT NULL,  -- the type of bee
    nobility nobility NOT NULL DEFAULT 'Drone',  -- the type of bee that this is
    speed INTEGER NOT NULL DEFAULT 0,  -- how often they produce honey
    fertility INTEGER NOT NULL DEFAULT 0,  -- how many drones spawn on their death
    generation INTEGER NOT NULL DEFAULT 0,  -- how many generations this bee has been alive for
    UNIQUE (owner_id, name)
);
