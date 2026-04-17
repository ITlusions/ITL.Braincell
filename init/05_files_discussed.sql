-- Files discussed

CREATE TABLE IF NOT EXISTS files_discussed (
    id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path        TEXT        NOT NULL UNIQUE,
    description      TEXT,
    language         VARCHAR(50),
    purpose          TEXT,
    last_modified    TIMESTAMP,
    discussion_count INTEGER     DEFAULT 1,
    created_at       TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    metadata         JSONB       DEFAULT '{}'::jsonb,
    -- retention
    retention_days   INTEGER     NOT NULL DEFAULT 30,
    retain_reason    VARCHAR(500),
    expires_at       TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_files_path             ON files_discussed(file_path);
CREATE INDEX IF NOT EXISTS idx_files_language         ON files_discussed(language);
CREATE INDEX IF NOT EXISTS idx_files_discussion_count ON files_discussed(discussion_count DESC);
CREATE INDEX IF NOT EXISTS idx_files_discussed_expires_at ON files_discussed(expires_at) WHERE expires_at IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_files_updated_at') THEN
        CREATE TRIGGER update_files_updated_at
            BEFORE UPDATE ON files_discussed
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
