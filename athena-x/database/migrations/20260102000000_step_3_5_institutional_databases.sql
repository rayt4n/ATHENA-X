-- ============================================================================
-- STEP 3.5 Migration: 12 schemas (10 institutional + 2 infrastructure)
-- Replaces the 4-schema layout from STEP 3.
-- Run order: this file first, then the 11 schema files below in order.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS raw_landing;
CREATE SCHEMA IF NOT EXISTS market_db;
CREATE SCHEMA IF NOT EXISTS options_db;
CREATE SCHEMA IF NOT EXISTS news_db;
CREATE SCHEMA IF NOT EXISTS macro_db;
CREATE SCHEMA IF NOT EXISTS validation_db;
CREATE SCHEMA IF NOT EXISTS ai_db;
CREATE SCHEMA IF NOT EXISTS forecast_db;
CREATE SCHEMA IF NOT EXISTS historical_db;
CREATE SCHEMA IF NOT EXISTS market_replay_db;
CREATE SCHEMA IF NOT EXISTS ai_memory_db;
CREATE SCHEMA IF NOT EXISTS app;

COMMENT ON SCHEMA raw_landing       IS 'Layer 1 raw provider payloads';
COMMENT ON SCHEMA market_db         IS 'Layer 4 Database 1 — Market (writer: standardization.market)';
COMMENT ON SCHEMA options_db        IS 'Layer 4 Database 2 — Options (writer: standardization.options)';
COMMENT ON SCHEMA news_db           IS 'Layer 4 Database 3 — News (writer: standardization.news)';
COMMENT ON SCHEMA macro_db          IS 'Layer 4 Database 4 — Macro (writer: standardization.macro)';
COMMENT ON SCHEMA validation_db     IS 'Layer 4 Database 5 — Validation (writers: validation agents)';
COMMENT ON SCHEMA ai_db             IS 'Layer 4 Database 6 — AI Intelligence (writers: intelligence agents)';
COMMENT ON SCHEMA forecast_db       IS 'Layer 4 Database 7 — Forecasts + Decisions (writers: decision agents)';
COMMENT ON SCHEMA historical_db     IS 'Layer 4 Database 8 — Historical Reports + Backtests (writers: report-engine, validator-engine)';
COMMENT ON SCHEMA market_replay_db  IS 'Layer 4 Database 9 — Market Replay (writer: market-replay-recorder)';
COMMENT ON SCHEMA ai_memory_db      IS 'Layer 4 Database 10 — AI Memory (writers: self-correction agents)';
COMMENT ON SCHEMA app               IS 'User workspaces, watchlists, module instances';
