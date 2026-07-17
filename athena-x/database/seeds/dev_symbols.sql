-- Dev seed data: default watchlist symbols (STEP 3.5)
INSERT INTO app.workspaces (user_id, name, main_indicator)
VALUES ('00000000-0000-0000-0000-000000000000', 'Default', 'SPY')
ON CONFLICT DO NOTHING;

INSERT INTO app.watchlists (workspace_id, symbol, asset_class, position) VALUES
    ('00000000-0000-0000-0000-000000000000', 'NVDA', 'equity', 1),
    ('00000000-0000-0000-0000-000000000000', 'AAPL', 'equity', 2),
    ('00000000-0000-0000-0000-000000000000', 'MSFT', 'equity', 3),
    ('00000000-0000-0000-0000-000000000000', 'TSLA', 'equity', 4),
    ('00000000-0000-0000-0000-000000000000', 'SPY',  'etf',    5),
    ('00000000-0000-0000-0000-000000000000', 'QQQ',  'etf',    6)
ON CONFLICT DO NOTHING;
