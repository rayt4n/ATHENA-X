-- ============================================================================
-- ai_memory_db — Layer 4 Database 10: AI Memory (NEW)
-- Writer: self-correction division agents ONLY
-- Purpose: Store what the AI concluded, why, and whether it was right.
--          Enables continuous self-improvement.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS ai_memory_db;

-- Every prediction ever made
CREATE TABLE IF NOT EXISTS ai_memory_db.predictions (
    prediction_id     UUID PRIMARY KEY,
    timestamp         TIMESTAMPTZ NOT NULL,
    agent_id          TEXT NOT NULL,
    model_id          TEXT,
    symbol            TEXT NOT NULL,
    prediction_type   TEXT NOT NULL,           -- 'price'|'direction'|'regime'|'probability'
    prediction_value  JSONB NOT NULL,
    horizon           TEXT NOT NULL,           -- '1D'|'1W'|'1M'
    reason            TEXT,
    evidence          JSONB,
    confidence        NUMERIC NOT NULL,
    -- Outcome (filled in later when the horizon elapses)
    actual_value      JSONB,
    outcome_timestamp TIMESTAMPTZ,
    error             NUMERIC,
    absolute_error    NUMERIC,
    squared_error     NUMERIC,
    -- Learning signal
    lessons_learned   JSONB
);
CREATE INDEX idx_predictions_agent_time ON ai_memory_db.predictions (agent_id, timestamp DESC);
CREATE INDEX idx_predictions_symbol_time ON ai_memory_db.predictions (symbol, timestamp DESC);
CREATE INDEX idx_predictions_unscored   ON ai_memory_db.predictions (timestamp) WHERE actual_value IS NULL;

-- Rolling accuracy per agent per period
CREATE TABLE IF NOT EXISTS ai_memory_db.agent_performance (
    agent_id          TEXT NOT NULL,
    period            TEXT NOT NULL,           -- '7d'|'30d'|'90d'|'all'
    accuracy          NUMERIC,
    precision         NUMERIC,
    recall            NUMERIC,
    sharpe            NUMERIC,
    max_drawdown      NUMERIC,
    sample_count      INTEGER,
    computed_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (agent_id, period, computed_at)
);

-- Lessons the AI has derived (and whether they've been applied)
CREATE TABLE IF NOT EXISTS ai_memory_db.lessons (
    lesson_id         BIGSERIAL PRIMARY KEY,
    timestamp         TIMESTAMPTZ NOT NULL DEFAULT now(),
    lesson_type       TEXT NOT NULL,           -- 'indicator-reliability'|'model-regime-fit'|'fomc-failure'|...
    description       TEXT NOT NULL,
    evidence          JSONB,
    applied           BOOLEAN DEFAULT false,
    applied_at        TIMESTAMPTZ
);

-- Answers to "which indicator/model/combination works best in which context"
CREATE TABLE IF NOT EXISTS ai_memory_db.insights (
    insight_id        BIGSERIAL PRIMARY KEY,
    generated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    question          TEXT NOT NULL,           -- e.g., "which model performs best in trending markets?"
    answer            TEXT NOT NULL,
    supporting_data   JSONB,
    confidence        NUMERIC NOT NULL
);
