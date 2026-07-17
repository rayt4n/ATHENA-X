-- ============================================================================
-- Row-Level Security policies (STEP 3.5)
-- ============================================================================

-- User-owned tables (workspaces, watchlists, module_instances, reports, backtests)
ALTER TABLE app.workspaces               ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.watchlists               ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.module_instances         ENABLE ROW LEVEL SECURITY;
ALTER TABLE historical_db.reports        ENABLE ROW LEVEL SECURITY;
ALTER TABLE historical_db.backtests      ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users own workspaces" ON app.workspaces
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY "users own watchlists" ON app.watchlists
    USING (EXISTS (SELECT 1 FROM app.workspaces WHERE id = workspace_id AND user_id = auth.uid()));
CREATE POLICY "users own module_instances" ON app.module_instances
    USING (EXISTS (SELECT 1 FROM app.workspaces WHERE id = workspace_id AND user_id = auth.uid()));
CREATE POLICY "users own reports" ON historical_db.reports
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY "users own backtests" ON historical_db.backtests
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- Read-only access to all Layer 4 databases for authenticated users
-- (write access is locked to service role, which bypasses RLS)
CREATE POLICY "authenticated read market_db"     ON market_db.quotes       FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read options_db"    ON options_db.chains      FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read news_db"       ON news_db.headlines      FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read macro_db"      ON macro_db.indicators    FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read validation_db" ON validation_db.decisions FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read ai_db"         ON ai_db.ta_signals       FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read forecast_db"   ON forecast_db.regimes    FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read replay_db"     ON market_replay_db.minute_snapshots FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read memory_db"     ON ai_memory_db.predictions FOR SELECT TO authenticated USING (true);

-- Service role bypasses RLS (for backend agents).
-- Each agent connects with a service-role key restricted to its designated schema
-- via GRANT statements (below).

-- Per-agent writer grants (restrict service role per agent)
GRANT INSERT, UPDATE ON market_db.quotes         TO service_role;
GRANT INSERT, UPDATE ON options_db.chains        TO service_role;
GRANT INSERT, UPDATE ON news_db.headlines        TO service_role;
GRANT INSERT, UPDATE ON macro_db.indicators      TO service_role;
GRANT INSERT ON validation_db.decisions          TO service_role;
GRANT INSERT ON ai_db.ta_signals                 TO service_role;
GRANT INSERT ON ai_db.options_signals            TO service_role;
GRANT INSERT ON forecast_db.regimes              TO service_role;
GRANT INSERT ON forecast_db.trajectories         TO service_role;
GRANT INSERT ON historical_db.reports            TO service_role;
GRANT INSERT ON historical_db.backtests          TO service_role;
GRANT INSERT ON market_replay_db.minute_snapshots TO service_role;
GRANT INSERT ON ai_memory_db.predictions         TO service_role;
