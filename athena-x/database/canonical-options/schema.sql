-- ============================================================================
-- canonical_options - Layer 4 Database 2: Standardized Options Data
-- Writer: Options Standardization Agent ONLY (role_options_standardizer)
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS canonical_options;

CREATE TABLE IF NOT EXISTS canonical_options.chains (
    record_id           UUID NOT NULL DEFAULT gen_random_uuid(),
    symbol              TEXT NOT NULL,
    underlying          TEXT NOT NULL,
    expiry              DATE NOT NULL,
    strike              NUMERIC NOT NULL,
    option_type         TEXT NOT NULL,  -- 'call' | 'put'
    timestamp           TIMESTAMPTZ NOT NULL,
    market_timestamp    TIMESTAMPTZ NOT NULL,
    bid                 NUMERIC,
    ask                 NUMERIC,
    last_price          NUMERIC,
    volume              BIGINT,
    open_interest       BIGINT,
    implied_volatility  NUMERIC,
    delta               NUMERIC,
    gamma               NUMERIC,
    theta               NUMERIC,
    vega                NUMERIC,
    rho                 NUMERIC,
    source_provider     TEXT NOT NULL,
    schema_version      TEXT NOT NULL,
    superseded_by       UUID,
    written_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (record_id, market_timestamp)
) PARTITION BY RANGE (market_timestamp);

CREATE INDEX IF NOT EXISTS idx_chains_lookup ON canonical_options.chains (symbol, expiry, strike);
CREATE INDEX IF NOT EXISTS idx_chains_underlying ON canonical_options.chains (underlying, expiry);

COMMENT ON SCHEMA canonical_options IS 'Layer 4 Database 2 - Standardized Options. Writer: role_options_standardizer ONLY';
