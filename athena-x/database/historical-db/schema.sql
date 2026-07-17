-- ============================================================================
-- historical_db — Layer 4 Database 8: Historical Reports + Backtests
-- Writers: report-engine, validator-engine
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS historical_db;

CREATE TABLE IF NOT EXISTS historical_db.reports (
    id              UUID PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    symbol          TEXT NOT NULL,
    title           TEXT NOT NULL,
    audience        TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    sections        JSONB NOT NULL,
    markdown        TEXT NOT NULL,
    json_content    JSONB NOT NULL,
    pdf_path        TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'generating',
    validation_score NUMERIC,
    validation_checks JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ
);
CREATE INDEX idx_reports_user_time ON historical_db.reports (user_id, created_at DESC);
CREATE INDEX idx_reports_symbol    ON historical_db.reports (symbol, created_at DESC);

CREATE TABLE IF NOT EXISTS historical_db.backtests (
    id              UUID PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    strategy_id     TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    config          JSONB NOT NULL,
    equity_curve    JSONB NOT NULL,
    trade_history   JSONB NOT NULL,
    metrics         JSONB NOT NULL,
    calibration     JSONB,
    started_at      TIMESTAMPTZ NOT NULL,
    completed_at    TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'running'
);
CREATE INDEX idx_backtests_user_time ON historical_db.backtests (user_id, started_at DESC);
