-- Hubs
CREATE TABLE Team (
    team_id VARCHAR PRIMARY KEY,
    load_date DATE,
    source VARCHAR
);

CREATE TABLE Player (
    player_id VARCHAR PRIMARY KEY,
    load_date DATE,
    source VARCHAR
);

-- Hub Satellites

CREATE TABLE Team_name_alias_fpl_core_insights (
    team_id VARCHAR,
    name_variant VARCHAR,
    load_date DATE,
    effective_from DATE,
    effective_to DATE,
    is_active BOOLEAN,
    source VARCHAR
)