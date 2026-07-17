-- ============================================================================
-- raw_landing — Layer 1 raw payloads (provider output as-received)
-- Writer: any Layer 1 provider adapter
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS raw_landing;

CREATE TABLE IF NOT EXISTS raw_landing.provider_payloads (
    id              BIGSERIAL PRIMARY KEY,
    provider        TEXT NOT NULL,
    endpoint        TEXT NOT NULL,
    symbol          TEXT,
    payload         JSONB NOT NULL,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    ingest_id       UUID NOT NULL
);
CREATE INDEX idx_raw_payloads_provider_time ON raw_landing.provider_payloads (provider, received_at DESC);
CREATE INDEX idx_raw_payloads_symbol_time   ON raw_landing.provider_payloads (symbol, received_at DESC);

CREATE TABLE IF NOT EXISTS raw_landing.provider_calls (
    id              BIGSERIAL PRIMARY KEY,
    provider        TEXT NOT NULL,
    endpoint        TEXT NOT NULL,
    status_code     INTEGER,
    latency_ms      INTEGER,
    error           TEXT,
    called_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_provider_calls_time ON raw_landing.provider_calls (provider, called_at DESC);
