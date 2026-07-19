-- ============================================================================
-- forecast_db — Layer 4 Database 7: Forecasts + Decisions (Layer 6 outputs)
-- Writer: decision-intelligence agents
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS forecast_db;

CREATE TABLE IF NOT EXISTS forecast_db.regimes (
    symbol          TEXT NOT NULL,
    regime          TEXT NOT NULL,
    confidence      NUMERIC NOT NULL,
    evidence        JSONB,
    classified_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, classified_at)
);
CREATE INDEX idx_regimes_lookup ON forecast_db.regimes (symbol, classified_at DESC);

CREATE TABLE IF NOT EXISTS forecast_db.trajectories (
    id              UUID PRIMARY KEY,
    symbol          TEXT NOT NULL,
    model_id        TEXT NOT NULL,
    runtime         TEXT NOT NULL,
    horizon         TEXT NOT NULL,
    trajectory      JSONB NOT NULL,
    inference_ms    INTEGER NOT NULL,
    model_version   TEXT NOT NULL,
    confidence      NUMERIC NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_trajectories_lookup ON forecast_db.trajectories (symbol, model_id, created_at DESC);

CREATE TABLE IF NOT EXISTS forecast_db.scenarios (
    symbol          TEXT NOT NULL,
    bull            NUMERIC NOT NULL,
    base            NUMERIC NOT NULL,
    bear            NUMERIC NOT NULL,
    confidence      NUMERIC NOT NULL,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, computed_at)
);

CREATE TABLE IF NOT EXISTS forecast_db.expected_moves (
    symbol          TEXT NOT NULL,
    horizon         TEXT NOT NULL,
    expected_move   NUMERIC NOT NULL,
    confidence      NUMERIC NOT NULL,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, horizon, computed_at)
);

CREATE TABLE IF NOT EXISTS forecast_db.probability_trees (
    symbol          TEXT NOT NULL,
    tree            JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS forecast_db.ai_consensus (
    symbol          TEXT NOT NULL PRIMARY KEY,
    consensus       TEXT NOT NULL,
    agreement       NUMERIC NOT NULL,
    components      JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS forecast_db.simulations (
    id              UUID PRIMARY KEY,
    symbol          TEXT NOT NULL,
    config          JSONB NOT NULL,
    stats           JSONB NOT NULL,
    paths           JSONB,
    confidence      NUMERIC NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS forecast_db.timeframe_alignment (
    symbol          TEXT NOT NULL PRIMARY KEY,
    alignment_score NUMERIC NOT NULL,
    breakdown       JSONB NOT NULL,
    confidence      NUMERIC NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
