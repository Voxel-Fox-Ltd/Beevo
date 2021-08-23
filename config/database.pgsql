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
    comb TEXT
);
INSERT INTO bee_comb_type VALUES ('forest', 'honey') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('meadows', 'honey') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('modest', 'parched') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('tropical', 'silky') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('wintry', 'frozen') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('marshy', 'mossy') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('water', 'wet') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('rocky', 'rocky') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('embittered', 'simmering') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('marbled', 'honey') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('valiant', 'cocoa') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('steadfast', 'cocoa') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('common', 'honey') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('cultivated', 'honey') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('noble', 'dripping') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('majestic', 'dripping') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('imperial', 'dripping') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('dilligent', 'stringy') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('unweary', 'stringy') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('industrious', 'stringy') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('heroic', 'cocoa') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('sinister', 'simmering') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('fiendish', 'simmering') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('demonic', 'simmering') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('frugal', 'parched') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('austere', 'parched') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('exotic', 'silky') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('edenic', 'silky') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('icy', 'frozen') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('glacial', 'frozen') ON CONFLICT (type) DO NOTHING;
INSERT INTO bee_comb_type VALUES ('rural', 'wheaten') ON CONFLICT (type) DO NOTHING;


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
