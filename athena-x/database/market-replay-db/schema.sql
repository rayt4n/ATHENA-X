-- ============================================================================
-- market_replay_db — Layer 4 Database 9: Market Replay (NEW)
-- Writer: market-replay-recorder agent ONLY
-- Purpose: Store everything, every minute. For backtesting, AI training,
--          debugging decisions, improving forecasts.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS market_replay_db;

CREATE TABLE IF NOT EXISTS market_replay_db.minute_snapshots (
    snapshot_id      BIGSERIAL PRIMARY KEY,
    timestamp        TIMESTAMPTZ NOT NULL,
    trading_date     DATE NOT NULL,
    session          TEXT NOT NULL,           -- 'pre'|'regular'|'post'
    -- Cross-domain snapshot (each is a JSONB blob)
    market_snapshot  JSONB NOT NULL,          -- quotes for all tracked symbols
    options_snapshot JSONB,                   -- chains + greeks + IV
    news_snapshot    JSONB,                   -- headlines received this minute
    macro_snapshot   JSONB,                   -- macro indicators updated
    gamma_snapshot   JSONB,                   -- GEX + gamma flip per symbol
    darkpool_snapshot JSONB,                  -- dark pool prints
    breadth_snapshot JSONB,                   -- advance/decline, new highs/lows
    confidence       NUMERIC NOT NULL DEFAULT 1.0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_replay_date_time ON market_replay_db.minute_snapshots (trading_date, timestamp);
CREATE INDEX idx_replay_session    ON market_replay_db.minute_snapshots (trading_date, session);

-- Tick-level replay (for ultra-fine backtesting)
CREATE TABLE IF NOT EXISTS market_replay_db.tick_events (
    id               BIGSERIAL PRIMARY KEY,
    timestamp        TIMESTAMPTZ NOT NULL,
    symbol           TEXT NOT NULL,
    event_type       TEXT NOT NULL,           -- 'trade'|'quote'|'level2'|'news'|'option_print'
    payload          JSONB NOT NULL,
    confidence       NUMERIC NOT NULL DEFAULT 1.0
);
CREATE INDEX idx_replay_ticks_symbol_time ON market_replay_db.tick_events (symbol, timestamp);
CREATE INDEX idx_replay_ticks_time         ON market_replay_db.tick_events (timestamp);
