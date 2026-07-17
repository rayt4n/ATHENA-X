-- ============================================================================
-- Row-Level Security policies
-- ============================================================================

-- User-owned tables (workspaces, watchlists, module_instances, reports, backtests)
ALTER TABLE app.workspaces        ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.watchlists        ENABLE ROW LEVEL SECURITY;
ALTER TABLE app.module_instances  ENABLE ROW LEVEL SECURITY;
ALTER TABLE historical_reports.reports  ENABLE ROW LEVEL SECURITY;
ALTER TABLE historical_reports.backtests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users own workspaces" ON app.workspaces
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE POLICY "users own watchlists" ON app.watchlists
    USING (EXISTS (SELECT 1 FROM app.workspaces WHERE id = workspace_id AND user_id = auth.uid()));

CREATE POLICY "users own module_instances" ON app.module_instances
    USING (EXISTS (SELECT 1 FROM app.workspaces WHERE id = workspace_id AND user_id = auth.uid()));

CREATE POLICY "users own reports" ON historical_reports.reports
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE POLICY "users own backtests" ON historical_reports.backtests
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- Read-only access to market data and AI intelligence for authenticated users
CREATE POLICY "authenticated read raw_market_data" ON raw_market_data.quotes
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read processed_market_data" ON processed_market_data.quotes
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "authenticated read ai_intelligence" ON ai_intelligence.ta_signals
    FOR SELECT TO authenticated USING (true);

-- Service role bypasses RLS (for backend agents)
-- (Supabase service role automatically bypasses RLS by default.)
