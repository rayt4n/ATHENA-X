-- ============================================================================
-- ai_db — Layer 4 Database 6: AI Intelligence (Layer 5 outputs)
-- Writer: each intelligence agent owns its own tables
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS ai_db;

CREATE TABLE IF NOT EXISTS ai_db.ta_signals (
    id              BIGSERIAL PRIMARY KEY,
    agent_id        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    direction       TEXT NOT NULL,
    strength        TEXT NOT NULL,
    weight          NUMERIC NOT NULL,
    confidence      NUMERIC NOT NULL,
    evidence        JSONB,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ta_signals_lookup ON ai_db.ta_signals (agent_id, symbol, emitted_at DESC);

CREATE TABLE IF NOT EXISTS ai_db.options_signals (
    id              BIGSERIAL PRIMARY KEY,
    agent_id        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    signal_type     TEXT NOT NULL,
    value           JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_options_signals_lookup ON ai_db.options_signals (agent_id, symbol, emitted_at DESC);

CREATE TABLE IF NOT EXISTS ai_db.news_signals (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    sentiment       TEXT NOT NULL,
    impact          INTEGER NOT NULL,
    confidence      NUMERIC NOT NULL,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_db.macro_signals (
    id              BIGSERIAL PRIMARY KEY,
    indicator       TEXT NOT NULL,
    region          TEXT NOT NULL,
    value           NUMERIC NOT NULL,
    trend           TEXT,
    confidence      NUMERIC NOT NULL,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_db.cross_market_signals (
    symbol          TEXT NOT NULL PRIMARY KEY,
    state           JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_db.agent_health (
    agent_id        TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT now(),
    running         BOOLEAN NOT NULL,
    cpu             NUMERIC,
    memory          NUMERIC,
    api_latency     NUMERIC,
    queue_length    INTEGER,
    error_count     INTEGER,
    restart_count   INTEGER,
    confidence      NUMERIC,
    version         TEXT,
    PRIMARY KEY (agent_id, timestamp)
);

-- Model weight table (managed by self-correction division)
CREATE TABLE IF NOT EXISTS ai_db.model_weights (
    model_id        TEXT PRIMARY KEY,
    weight          NUMERIC NOT NULL,
    accuracy_7d     NUMERIC,
    accuracy_30d    NUMERIC,
    sample_count    INTEGER NOT NULL DEFAULT 0,
    last_adjusted_at TIMESTAMPTZ,
    last_adjustment_reason TEXT
);
