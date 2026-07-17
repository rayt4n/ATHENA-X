-- ATHENA-X initial migration — creates all four schemas + app schema.
-- Run order: this file first, then the four schema files in dependency order:
--   1. raw-market-data/schema.sql
--   2. processed-market-data/schema.sql
--   3. ai-intelligence/schema.sql
--   4. historical-reports/schema.sql

CREATE SCHEMA IF NOT EXISTS raw_market_data;
CREATE SCHEMA IF NOT EXISTS processed_market_data;
CREATE SCHEMA IF NOT EXISTS ai_intelligence;
CREATE SCHEMA IF NOT EXISTS historical_reports;
CREATE SCHEMA IF NOT EXISTS app;

COMMENT ON SCHEMA raw_market_data IS 'Untouched provider output. Writer: collection-agent only.';
COMMENT ON SCHEMA processed_market_data IS 'Normalized + validated market data. Writer: standardization-agent only.';
COMMENT ON SCHEMA ai_intelligence IS 'Agent outputs, predictions, signals, weights. Each agent owns its tables.';
COMMENT ON SCHEMA historical_reports IS 'Generated reports + backtests. Writers: report-engine, validator-engine.';
COMMENT ON SCHEMA app IS 'User-facing app data: workspaces, watchlists, module instances.';
