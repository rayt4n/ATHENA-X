-- ============================================================================
-- Database 4: historical_reports
-- Generated reports + backtests. Writers: report-engine, validator-engine.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS historical_reports;

-- Generated reports (4 artifacts: markdown + json + pdf + storage path)
CREATE TABLE IF NOT EXISTS historical_reports.reports (
    id              UUID PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    symbol          TEXT NOT NULL,
    title           TEXT NOT NULL,
    audience        TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    sections        JSONB NOT NULL,
    markdown        TEXT NOT NULL,                  -- canonical format
    json_content    JSONB NOT NULL,                 -- structured
    pdf_path        TEXT NOT NULL,                  -- Supabase Storage path
    status          TEXT NOT NULL DEFAULT 'generating',  -- generating|completed|approved|rejected
    validation_score NUMERIC,
    validation_checks JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ
);
CREATE INDEX idx_reports_user_time ON historical_reports.reports (user_id, created_at DESC);
CREATE INDEX idx_reports_symbol    ON historical_reports.reports (symbol, created_at DESC);

-- Backtests (real vectorbt results)
CREATE TABLE IF NOT EXISTS historical_reports.backtests (
    id              UUID PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    strategy_id     TEXT NOT NULL,
    symbol          TEXT NOT NULL,
    config          JSONB NOT NULL,
    equity_curve    JSONB NOT NULL,
    trade_history   JSONB NOT NULL,
    metrics         JSONB NOT NULL,    -- { returns, sharpe, sortino, max_dd, calmar, win_rate, ... }
    calibration     JSONB,
    started_at      TIMESTAMPTZ NOT NULL,
    completed_at    TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'running'
);
CREATE INDEX idx_backtests_user_time ON historical_reports.backtests (user_id, started_at DESC);

-- User workspaces (per-user, workspace-aware — Change 7 of original STEP 2)
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    main_indicator  TEXT NOT NULL DEFAULT 'SPY' CHECK (main_indicator IN ('ES', 'SPY')),
    panel_layout    JSONB NOT NULL DEFAULT '[]'::jsonb,
    background_services JSONB NOT NULL DEFAULT '[]'::jsonb,
    settings        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.watchlists (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES app.workspaces (id) ON DELETE CASCADE,
    symbol          TEXT NOT NULL,
    asset_class     TEXT NOT NULL,
    position        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS app.module_instances (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES app.workspaces (id) ON DELETE CASCADE,
    module_id       TEXT NOT NULL,
    config          JSONB NOT NULL DEFAULT '{}'::jsonb,
    state           JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Model registry (AI model artifacts, browser-onnx + python-gpu)
CREATE TABLE IF NOT EXISTS ai_intelligence.model_artifacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id        TEXT NOT NULL,
    version         TEXT NOT NULL,
    runtime         TEXT NOT NULL,    -- python-gpu|browser-onnx
    storage_path    TEXT NOT NULL,
    input_schema    JSONB NOT NULL,
    output_schema   JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (model_id, version)
);
