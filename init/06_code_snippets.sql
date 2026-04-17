-- Code snippets

CREATE TABLE IF NOT EXISTS code_snippets (
    id             UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    title          TEXT        NOT NULL,
    code_content   TEXT        NOT NULL,
    language       VARCHAR(50),
    file_path      TEXT,
    line_start     INTEGER,
    line_end       INTEGER,
    description    TEXT,
    tags           TEXT[]      DEFAULT '{}',
    created_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    metadata       JSONB       DEFAULT '{}'::jsonb,
    -- retention (0 = keep forever)
    retention_days INTEGER     NOT NULL DEFAULT 0,
    retain_reason  VARCHAR(500),
    expires_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_snippets_language   ON code_snippets(language);
CREATE INDEX IF NOT EXISTS idx_snippets_file       ON code_snippets(file_path);
CREATE INDEX IF NOT EXISTS idx_snippets_tags       ON code_snippets USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_code_snippets_expires_at ON code_snippets(expires_at) WHERE expires_at IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_snippets_updated_at') THEN
        CREATE TRIGGER update_snippets_updated_at
            BEFORE UPDATE ON code_snippets
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
