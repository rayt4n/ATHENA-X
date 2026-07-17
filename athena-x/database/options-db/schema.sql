-- ============================================================================
-- options_db — Layer 4 Database 2: Options
-- Writer: standardization.options ONLY
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS options_db;

CREATE TABLE IF NOT EXISTS options_db.chains (
    symbol          TEXT NOT NULL,
    expiry          DATE NOT NULL,
    chain           JSONB NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, expiry)
);

CREATE TABLE IF NOT EXISTS options_db.greeks (
    symbol          TEXT NOT NULL,
    strike          NUMERIC NOT NULL,
    expiry          DATE NOT NULL,
    option_type     TEXT NOT NULL,
    delta           NUMERIC,
    gamma           NUMERIC,
    theta           NUMERIC,
    vega            NUMERIC,
    rho             NUMERIC,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, strike, expiry, option_type)
);

CREATE TABLE IF NOT EXISTS options_db.iv_surface (
    symbol          TEXT NOT NULL,
    strike          NUMERIC NOT NULL,
    expiry          DATE NOT NULL,
    iv              NUMERIC NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, strike, expiry)
);

CREATE TABLE IF NOT EXISTS options_db.open_interest (
    symbol          TEXT NOT NULL,
    strike          NUMERIC NOT NULL,
    expiry          DATE NOT NULL,
    call_oi         BIGINT,
    put_oi          BIGINT,
    call_vol        BIGINT,
    put_vol         BIGINT,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, strike, expiry)
);
