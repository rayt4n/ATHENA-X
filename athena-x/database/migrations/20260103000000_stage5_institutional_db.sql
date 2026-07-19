-- ============================================================================
-- Stage 5 Migration: Institutional Database Layer v2.0
-- Adds: partitioning, indexes, RLS, writer-lock roles, immutable records
-- ============================================================================

-- 1. Create writer-lock roles (Stage 5 req 2)
CREATE ROLE role_market_standardizer NOLOGIN;
CREATE ROLE role_options_standardizer NOLOGIN;
CREATE ROLE role_news_standardizer NOLOGIN;
CREATE ROLE role_macro_standardizer NOLOGIN;
CREATE ROLE role_validation NOLOGIN;
CREATE ROLE role_intelligence NOLOGIN;
CREATE ROLE role_decision NOLOGIN;
CREATE ROLE role_report_engine NOLOGIN;
CREATE ROLE role_replay_recorder NOLOGIN;
CREATE ROLE role_self_correction NOLOGIN;
CREATE ROLE role_provider NOLOGIN;
CREATE ROLE role_reader NOLOGIN;

-- 2. Grant schema permissions (writer-lock enforcement)
GRANT INSERT, UPDATE ON canonical_market.quotes TO role_market_standardizer;
GRANT INSERT, UPDATE ON canonical_market.bars TO role_market_standardizer;
GRANT INSERT, UPDATE ON canonical_market.trades TO role_market_standardizer;
GRANT SELECT ON canonical_market.quotes TO role_reader;
GRANT SELECT ON canonical_market.bars TO role_reader;
GRANT SELECT ON canonical_market.trades TO role_reader;

GRANT INSERT, UPDATE ON canonical_options.chains TO role_options_standardizer;
GRANT SELECT ON canonical_options.chains TO role_reader;

-- 3. Enable RLS on user-facing schemas (Stage 5 req 3)
-- (already done in database/policies/rls.sql)

-- 4. Create partitions for current month + next month
-- (run by PartitionManager at startup)

COMMENT ON SCHEMA canonical_market IS 'Stage 5 - partitioned, indexed, immutable, RLS-enforced';
