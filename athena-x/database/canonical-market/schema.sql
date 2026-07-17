-- ============================================================================
-- canonical_market - Layer 4 Database 1: Standardized Market Data
-- Writer: Market Standardization Agent ONLY (role_market_standardizer)
-- Stage 5: partitioned + indexed + immutable + RLS
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS canonical_market;

-- Quotes table (partitioned monthly)
CREATE TABLE IF NOT EXISTS canonical_market.quotes (
    record_id           UUID NOT NULL DEFAULT gen_random_uuid(),
    symbol              TEXT NOT NULL,
    asset_class         TEXT NOT NULL,
    exchange            TEXT,
    timestamp           TIMESTAMPTZ NOT NULL,
    market_timestamp    TIMESTAMPTZ NOT NULL,
    session             TEXT NOT NULL,
    trading_day         DATE,
    exchange_local_time TIMESTAMPTZ,
    last_price          NUMERIC NOT NULL,
    open                NUMERIC,
    high                NUMERIC,
    low                 NUMERIC,
    close               NUMERIC,
    bid                 NUMERIC,
    ask                 NUMERIC,
    volume              BIGINT,
    currency            TEXT DEFAULT 'USD',
    market              TEXT,
    sector              TEXT,
    industry            TEXT,
    region              TEXT,
    -- Provenance
    source_provider     TEXT NOT NULL,
    raw_payload_id      TEXT,
    validation_id       TEXT,
    transformation_id   TEXT,
    -- Versioning
    schema_version      TEXT NOT NULL,
    mapping_version     TEXT NOT NULL,
    provider_version    TEXT,
    -- Metadata
    provider_metadata   JSONB DEFAULT '{}'::jsonb,
    validation_metadata JSONB DEFAULT '{}'::jsonb,
    -- Immutable records (Stage 5 req 7)
    superseded_by       UUID,  -- if non-null, this record is superseded
    supersedes          UUID,  -- if non-null, this record supersedes another
    written_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (record_id, market_timestamp)
) PARTITION BY RANGE (market_timestamp);

-- Indexes (Stage 5 req 5)
CREATE INDEX IF NOT EXISTS idx_quotes_symbol_time ON canonical_market.quotes (symbol, market_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_quotes_session ON canonical_market.quotes (symbol, session, market_timestamp);
CREATE INDEX IF NOT EXISTS idx_quotes_provider ON canonical_market.quotes (source_provider, market_timestamp);

-- Bars table (partitioned monthly)
CREATE TABLE IF NOT EXISTS canonical_market.bars (
    record_id           UUID NOT NULL DEFAULT gen_random_uuid(),
    symbol              TEXT NOT NULL,
    timeframe           TEXT NOT NULL,
    timestamp           BIGINT NOT NULL,  -- unix-millis
    market_timestamp    TIMESTAMPTZ NOT NULL,
    open                NUMERIC NOT NULL,
    high                NUMERIC NOT NULL,
    low                 NUMERIC NOT NULL,
    close               NUMERIC NOT NULL,
    volume              BIGINT NOT NULL,
    source_provider     TEXT NOT NULL,
    schema_version      TEXT NOT NULL,
    superseded_by       UUID,
    written_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (record_id, market_timestamp)
) PARTITION BY RANGE (market_timestamp);

CREATE INDEX IF NOT EXISTS idx_bars_lookup ON canonical_market.bars (symbol, timeframe, market_timestamp DESC);

-- Trades table (partitioned DAILY - high frequency)
CREATE TABLE IF NOT EXISTS canonical_market.trades (
    record_id           UUID NOT NULL DEFAULT gen_random_uuid(),
    symbol              TEXT NOT NULL,
    price               NUMERIC NOT NULL,
    size                INTEGER NOT NULL,
    side                TEXT,
    market_timestamp    TIMESTAMPTZ NOT NULL,
    source_provider     TEXT NOT NULL,
    written_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (record_id, market_timestamp)
) PARTITION BY RANGE (market_timestamp);

CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON canonical_market.trades (symbol, market_timestamp);

COMMENT ON SCHEMA canonical_market IS 'Layer 4 Database 1 - Standardized Market Data. Writer: role_market_standardizer ONLY';
