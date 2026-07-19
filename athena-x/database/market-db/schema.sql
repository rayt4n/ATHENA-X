-- ============================================================================
-- market_db — Layer 4 Database 1: Market
-- Writer: standardization.market ONLY
-- Reader: technical-analysis, options-intelligence, macro-intelligence, decision-intelligence
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS market_db;

CREATE TABLE IF NOT EXISTS market_db.quotes (
    symbol          TEXT NOT NULL PRIMARY KEY,
    last_price      NUMERIC NOT NULL,
    bid             NUMERIC,
    ask             NUMERIC,
    high            NUMERIC,
    low             NUMERIC,
    open            NUMERIC,
    prev_close      NUMERIC,
    volume          BIGINT,
    change          NUMERIC,
    change_percent  NUMERIC,
    -- Layer 2 validation metadata
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    source_count    INTEGER NOT NULL DEFAULT 1,
    validation_status TEXT NOT NULL DEFAULT 'verified',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS market_db.bars (
    symbol          TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    timestamp       BIGINT NOT NULL,
    open            NUMERIC NOT NULL,
    high            NUMERIC NOT NULL,
    low             NUMERIC NOT NULL,
    close           NUMERIC NOT NULL,
    volume          BIGINT NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, timeframe, timestamp)
);

CREATE TABLE IF NOT EXISTS market_db.trades (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    price           NUMERIC NOT NULL,
    size            INTEGER NOT NULL,
    side            TEXT,
    timestamp       BIGINT NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_trades_symbol_time ON market_db.trades (symbol, timestamp DESC);

CREATE TABLE IF NOT EXISTS market_db.cross_market_state (
    symbol          TEXT NOT NULL PRIMARY KEY,
    state           JSONB NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
