-- ============================================================================
-- app — User-facing application data
-- Writers: frontend (via Supabase Auth + RLS)
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    main_indicator  TEXT NOT NULL DEFAULT 'SPY' CHECK (main_indicator IN ('ES', 'SPY')),
    panel_layout    JSONB NOT NULL DEFAULT '[]'::jsonb,
    background_services JSONB NOT NULL DEFAULT '[]'::jsonb,
    settings        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.watchlists (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES app.workspaces (id) ON DELETE CASCADE,
    symbol          TEXT NOT NULL,
    asset_class     TEXT NOT NULL,
    position        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS app.module_instances (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES app.workspaces (id) ON DELETE CASCADE,
    module_id       TEXT NOT NULL,
    config          JSONB NOT NULL DEFAULT '{}'::jsonb,
    state           JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Model registry (AI model artifacts)
CREATE TABLE IF NOT EXISTS app.model_artifacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id        TEXT NOT NULL,
    version         TEXT NOT NULL,
    runtime         TEXT NOT NULL,
    storage_path    TEXT NOT NULL,
    input_schema    JSONB NOT NULL,
    output_schema   JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (model_id, version)
);
