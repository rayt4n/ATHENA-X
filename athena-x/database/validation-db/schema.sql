-- ============================================================================
-- validation_db — Layer 4 Database 5: Validation
-- Writer: validation agents (each writes its own tables)
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS validation_db;

CREATE TABLE IF NOT EXISTS validation_db.decisions (
    id              BIGSERIAL PRIMARY KEY,
    validator       TEXT NOT NULL,
    symbol          TEXT,
    payload_hash    TEXT NOT NULL,
    status          TEXT NOT NULL,    -- verified|rejected|degraded
    confidence      NUMERIC NOT NULL,
    sources_checked INTEGER NOT NULL,
    sources_agreed  INTEGER NOT NULL,
    outlier_source  TEXT,
    reason          TEXT,
    decided_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_validation_decisions_lookup ON validation_db.decisions (validator, symbol, decided_at DESC);

CREATE TABLE IF NOT EXISTS validation_db.provider_reliability (
    provider        TEXT NOT NULL,
    date            DATE NOT NULL,
    total_calls     INTEGER NOT NULL DEFAULT 0,
    successful_calls INTEGER NOT NULL DEFAULT 0,
    failed_calls    INTEGER NOT NULL DEFAULT 0,
    avg_latency_ms  NUMERIC,
    reliability_score NUMERIC NOT NULL DEFAULT 1.0,
    PRIMARY KEY (provider, date)
);

CREATE TABLE IF NOT EXISTS validation_db.quality_scores (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    domain          TEXT NOT NULL,    -- market|options|news|macro
    quality_score   NUMERIC NOT NULL,
    issues          JSONB,
    checked_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_quality_scores_lookup ON validation_db.quality_scores (symbol, domain, checked_at DESC);
