-- ============================================================================
-- Database 3: ai_intelligence
-- Agent outputs, predictions, signals, weights. Each agent owns its tables.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS ai_intelligence;

-- Technical Analysis signals (one row per agent×symbol×timeframe)
CREATE TABLE IF NOT EXISTS ai_intelligence.ta_signals (
    id              BIGSERIAL PRIMARY KEY,
    agent_id        TEXT NOT NULL,    -- e.g., 'ta.rsi', 'ta.macd'
    symbol          TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    direction       TEXT NOT NULL,    -- long|short|neutral
    strength        TEXT NOT NULL,    -- weak|moderate|strong
    weight          NUMERIC NOT NULL,
    confidence      NUMERIC NOT NULL,
    evidence        JSONB,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ta_signals_lookup ON ai_intelligence.ta_signals (agent_id, symbol, emitted_at DESC);

-- Options Intelligence signals
CREATE TABLE IF NOT EXISTS ai_intelligence.options_signals (
    id              BIGSERIAL PRIMARY KEY,
    agent_id        TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    signal_type     TEXT NOT NULL,    -- greeks|iv|skew|gamma|max-pain|...
    value           JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_options_signals_lookup ON ai_intelligence.options_signals (agent_id, symbol, emitted_at DESC);

-- News signals
CREATE TABLE IF NOT EXISTS ai_intelligence.news_signals (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    sentiment       TEXT NOT NULL,
    impact          INTEGER NOT NULL,
    confidence      NUMERIC NOT NULL,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Macro signals
CREATE TABLE IF NOT EXISTS ai_intelligence.macro_signals (
    id              BIGSERIAL PRIMARY KEY,
    indicator       TEXT NOT NULL,
    region          TEXT NOT NULL,
    value           NUMERIC NOT NULL,
    trend           TEXT,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Cross-market signals (per instrument)
CREATE TABLE IF NOT EXISTS ai_intelligence.cross_market_signals (
    symbol          TEXT NOT NULL PRIMARY KEY,
    state           JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Market regime classifications
CREATE TABLE IF NOT EXISTS ai_intelligence.regimes (
    symbol          TEXT NOT NULL,
    regime          TEXT NOT NULL,
    confidence      NUMERIC NOT NULL,
    evidence        JSONB,
    classified_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, classified_at)
);
CREATE INDEX idx_regimes_lookup ON ai_intelligence.regimes (symbol, classified_at DESC);

-- Forecasts (per model run)
CREATE TABLE IF NOT EXISTS ai_intelligence.forecasts (
    id              UUID PRIMARY KEY,
    symbol          TEXT NOT NULL,
    model_id        TEXT NOT NULL,
    runtime         TEXT NOT NULL,    -- python-gpu|browser-onnx
    horizon         TEXT NOT NULL,
    trajectory      JSONB NOT NULL,   -- array of {t, price, confidence}
    inference_ms    INTEGER NOT NULL,
    model_version   TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_forecasts_lookup ON ai_intelligence.forecasts (symbol, model_id, created_at DESC);

-- Probability simulations
CREATE TABLE IF NOT EXISTS ai_intelligence.simulations (
    id              UUID PRIMARY KEY,
    symbol          TEXT NOT NULL,
    config          JSONB NOT NULL,
    stats           JSONB NOT NULL,
    paths           JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Model weight table (managed by self-correction-engine)
CREATE TABLE IF NOT EXISTS ai_intelligence.model_weights (
    model_id        TEXT PRIMARY KEY,
    weight          NUMERIC NOT NULL,
    accuracy_7d     NUMERIC,
    accuracy_30d    NUMERIC,
    sample_count    INTEGER NOT NULL DEFAULT 0,
    last_adjusted_at TIMESTAMPTZ,
    last_adjustment_reason TEXT
);

-- Agent health history (for Agent Health Dashboard, Change 17)
CREATE TABLE IF NOT EXISTS ai_intelligence.agent_health (
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

-- Prediction scoring (self-correction)
CREATE TABLE IF NOT EXISTS ai_intelligence.prediction_scores (
    id              BIGSERIAL PRIMARY KEY,
    model_id        TEXT NOT NULL,
    prediction_id   UUID NOT NULL,
    symbol          TEXT NOT NULL,
    predicted       NUMERIC NOT NULL,
    actual          NUMERIC NOT NULL,
    error           NUMERIC NOT NULL,
    absolute_error  NUMERIC NOT NULL,
    scored_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_prediction_scores_model ON ai_intelligence.prediction_scores (model_id, scored_at DESC);

-- Supervisor decisions log
CREATE TABLE IF NOT EXISTS ai_intelligence.supervisor_decisions (
    id              BIGSERIAL PRIMARY KEY,
    decision_type   TEXT NOT NULL,    -- conflict-detected|agent-failing|retry-requested|confidence-adjusted
    agent_id        TEXT,
    symbol          TEXT,
    payload         JSONB NOT NULL,
    decided_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
