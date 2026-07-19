-- ============================================================================
-- macro_db — Layer 4 Database 4: Macro
-- Writer: standardization.macro ONLY
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS macro_db;

CREATE TABLE IF NOT EXISTS macro_db.indicators (
    indicator       TEXT NOT NULL,
    region          TEXT NOT NULL,
    frequency       TEXT NOT NULL,
    value           NUMERIC NOT NULL,
    previous        NUMERIC,
    surprise        NUMERIC,
    unit            TEXT,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    released_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (indicator, region, released_at)
);
CREATE INDEX idx_macro_indicators_lookup ON macro_db.indicators (indicator, region, released_at DESC);

CREATE TABLE IF NOT EXISTS macro_db.yield_curve (
    region          TEXT NOT NULL DEFAULT 'US',
    tenor           TEXT NOT NULL,
    yield           NUMERIC NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (region, tenor, updated_at)
);

CREATE TABLE IF NOT EXISTS macro_db.fx_rates (
    pair            TEXT NOT NULL PRIMARY KEY,
    rate            NUMERIC NOT NULL,
    change          NUMERIC,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS macro_db.commodities (
    commodity       TEXT NOT NULL PRIMARY KEY,
    price           NUMERIC NOT NULL,
    change          NUMERIC,
    unit            TEXT,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS macro_db.economic_calendar (
    id              BIGSERIAL PRIMARY KEY,
    event           TEXT NOT NULL,
    region          TEXT NOT NULL,
    scheduled_at    TIMESTAMPTZ NOT NULL,
    actual          NUMERIC,
    forecast        NUMERIC,
    previous        NUMERIC,
    surprise        NUMERIC,
    confidence      NUMERIC NOT NULL DEFAULT 1.0
);
CREATE INDEX idx_economic_calendar_time ON macro_db.economic_calendar (scheduled_at);
