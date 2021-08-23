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


CREATE TABLE IF NOT EXISTS bee_comb_type(
    type TEXT PRIMARY KEY,
    comb TEXT,
);
INSERT INTO bee_comb_type VALUES ('Forest', 'Honey') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Meadows', 'Honey') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Modest', 'Parched') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Tropical', 'Silky') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Wintry', 'Frozen') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Marshy', 'Mossy') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Water', 'Wet') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Rocky', 'Rocky') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Embittered', 'Simmering') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Marbled', 'Honey') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Valiant', 'Cocoa') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Steadfast', 'Cocoa') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Common', 'Honey') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Cultivated', 'Honey') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Noble', 'Dripping') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Majestic', 'Dripping') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Imperial', 'Dripping') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Dilligent', 'Stringy') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Unweary', 'Stringy') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Industrious', 'Stringy') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Heroic', 'Cocoa') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Sinister', 'Simmering') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Fiendish', 'Simmering') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Demonic', 'Simmering') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Frugal', 'Parched') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Austere', 'Parched') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Exotic', 'Silky') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Edenic', 'Silky') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Icy', 'Frozen') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Glacial', 'Frozen') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('Rural', 'Wheaten') ON CONFLICT (type) DO NOTHING;


CREATE TABLE IF NOT EXISTS user_inventory(
    user_id BIGINT,
    item_name CITEXT,
    quantity INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, item_name)
);


CREATE TABLE IF NOT EXISTS hives(
    id TEXT PRIMARY KEY,
    index SMALLINT,
    guild_id BIGINT,
    owner_id BIGINT
);


CREATE TABLE IF NOT EXISTS hive_inventory(
    hive_id TEXT REFERENCES hives(id),
    item_name CITEXT,
    quantity INTEGER DEFAULT 0,
    PRIMARY KEY (hive_id, item_name)
);


CREATE TABLE IF NOT EXISTS bees(
    id TEXT PRIMARY KEY,  -- the bee identifier
    parent_ids TEXT[],  -- the parents of the bees
    guild_id BIGINT,  -- the ID of the guild that the bee belongs to
    owner_id BIGINT,  -- the ID of the user who owns the bee
    hive_id TEXT REFERENCES hives(id),  -- the ID of the hive that the bee lives in
    name CITEXT,  -- the name given to the bee
    type TEXT NOT NULL,  -- the type of bee
    nobility nobility NOT NULL DEFAULT 'Drone',  -- the type of bee that this is
    speed INTEGER NOT NULL DEFAULT 1,  -- how often they produce honey (percent chance per tick)
    fertility INTEGER NOT NULL DEFAULT 1,  -- how many drones spawn on their death (min 1 max 10)
    lifetime INTEGER NOT NULL DEFAULT 180,  -- how long the bee stays alive for (in ticks)
    lived_lifetime INTEGER DEFAULT 0,  -- how many ticks this bee has been in a hive for
    UNIQUE (guild_id, owner_id, name)
);
