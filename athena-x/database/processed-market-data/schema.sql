-- ============================================================================
-- Database 2: processed_market_data
-- Normalized, deduplicated, validated. Writer: standardization-agent only.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS processed_market_data;

-- Canonical quotes (post-validation, post-dedup)
CREATE TABLE IF NOT EXISTS processed_market_data.quotes (
    symbol          TEXT NOT NULL,
    last            NUMERIC NOT NULL,
    bid             NUMERIC,
    ask             NUMERIC,
    high            NUMERIC,
    low             NUMERIC,
    open            NUMERIC,
    prev_close      NUMERIC,
    volume          BIGINT,
    change          NUMERIC,
    change_percent  NUMERIC,
    quality_score   NUMERIC NOT NULL,  -- 0..1 from validation-agent
    source_count    INTEGER NOT NULL,  -- how many providers contributed
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol)
);

-- Canonical OHLCV bars
CREATE TABLE IF NOT EXISTS processed_market_data.bars (
    symbol          TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    timestamp       BIGINT NOT NULL,  -- unix-millis
    open            NUMERIC NOT NULL,
    high            NUMERIC NOT NULL,
    low             NUMERIC NOT NULL,
    close           NUMERIC NOT NULL,
    volume          BIGINT NOT NULL,
    quality_score   NUMERIC NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, timeframe, timestamp)
);

-- Canonical trades
CREATE TABLE IF NOT EXISTS processed_market_data.trades (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    price           NUMERIC NOT NULL,
    size            INTEGER NOT NULL,
    side            TEXT,
    timestamp       BIGINT NOT NULL,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_trades_symbol_time ON processed_market_data.trades (symbol, timestamp DESC);

-- Canonical options chains
CREATE TABLE IF NOT EXISTS processed_market_data.option_chains (
    symbol          TEXT NOT NULL,
    expiry          DATE NOT NULL,
    chain           JSONB NOT NULL,
    quality_score   NUMERIC NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, expiry)
);

-- Canonical news (post-NLP)
CREATE TABLE IF NOT EXISTS processed_market_data.news (
    id              UUID PRIMARY KEY,
    symbol          TEXT,
    headline        TEXT NOT NULL,
    body            TEXT,
    url             TEXT,
    source          TEXT NOT NULL,
    category        TEXT,
    sentiment       TEXT,
    sentiment_score NUMERIC,
    impact          INTEGER,
    published_at    TIMESTAMPTZ,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_news_symbol_time ON processed_market_data.news (symbol, published_at DESC);

-- Data quality log
CREATE TABLE IF NOT EXISTS processed_market_data.data_quality (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    provider        TEXT NOT NULL,
    quality_score   NUMERIC NOT NULL,
    issues          JSONB,
    checked_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_quality_lookup ON processed_market_data.data_quality (symbol, checked_at DESC);
