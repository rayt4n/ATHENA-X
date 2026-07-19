-- ============================================================================
-- news_db — Layer 4 Database 3: News
-- Writer: standardization.news ONLY
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS news_db;

CREATE TABLE IF NOT EXISTS news_db.headlines (
    id              UUID PRIMARY KEY,
    headline        TEXT NOT NULL,
    body            TEXT,
    url             TEXT,
    source          TEXT NOT NULL,
    source_reputation NUMERIC NOT NULL DEFAULT 0.5,
    symbol          TEXT,
    category        TEXT,
    published_at    TIMESTAMPTZ,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_news_symbol_time ON news_db.headlines (symbol, published_at DESC);
CREATE INDEX idx_news_source_time ON news_db.headlines (source, published_at DESC);

CREATE TABLE IF NOT EXISTS news_db.sentiment (
    headline_id     UUID PRIMARY KEY REFERENCES news_db.headlines (id) ON DELETE CASCADE,
    sentiment       TEXT NOT NULL,
    score           NUMERIC NOT NULL,
    impact          INTEGER,
    model           TEXT NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS news_db.entities (
    id              BIGSERIAL PRIMARY KEY,
    headline_id     UUID REFERENCES news_db.headlines (id) ON DELETE CASCADE,
    entity          TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    extracted_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_news_entities_lookup ON news_db.entities (entity, extracted_at DESC);

CREATE TABLE IF NOT EXISTS news_db.fear_greed (
    id              BIGSERIAL PRIMARY KEY,
    value           INTEGER NOT NULL,
    classification  TEXT NOT NULL,
    source          TEXT NOT NULL DEFAULT 'cnn',
    confidence      NUMERIC NOT NULL DEFAULT 1.0,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
