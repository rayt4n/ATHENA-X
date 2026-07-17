-- ============================================================================
-- Database 1: raw_market_data
-- Untouched provider output. Writer: collection-agent only.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS raw_market_data;

-- Provider quotes as received
CREATE TABLE IF NOT EXISTS raw_market_data.quotes (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    provider        TEXT NOT NULL,
    payload         JSONB NOT NULL,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    ingest_id       UUID NOT NULL
);
CREATE INDEX idx_raw_quotes_symbol_time ON raw_market_data.quotes (symbol, received_at DESC);
CREATE INDEX idx_raw_quotes_provider   ON raw_market_data.quotes (provider, received_at DESC);

-- Raw bars
CREATE TABLE IF NOT EXISTS raw_market_data.bars (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    provider        TEXT NOT NULL,
    payload         JSONB NOT NULL,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_raw_bars_lookup ON raw_market_data.bars (symbol, timeframe, received_at DESC);

-- Raw trades
CREATE TABLE IF NOT EXISTS raw_market_data.trades (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    provider        TEXT NOT NULL,
    price           NUMERIC NOT NULL,
    size            INTEGER NOT NULL,
    side            TEXT,
    payload         JSONB,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Raw news (before NLP processing)
CREATE TABLE IF NOT EXISTS raw_market_data.news (
    id              UUID PRIMARY KEY,
    symbol          TEXT,
    provider        TEXT NOT NULL,
    headline        TEXT NOT NULL,
    body            TEXT,
    url             TEXT,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload         JSONB
);

-- Raw provider call log (for data quality dashboard)
CREATE TABLE IF NOT EXISTS raw_market_data.provider_calls (
    id              BIGSERIAL PRIMARY KEY,
    provider        TEXT NOT NULL,
    endpoint        TEXT NOT NULL,
    status_code     INTEGER,
    latency_ms      INTEGER,
    error           TEXT,
    called_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_provider_calls_time ON raw_market_data.provider_calls (provider, called_at DESC);
