-- Cell notes

CREATE TABLE IF NOT EXISTS cell_notes (
    id             UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    title          TEXT        NOT NULL,
    content        TEXT        NOT NULL,
    tags           TEXT[]      DEFAULT '{}',
    source         VARCHAR(100) DEFAULT 'agent',
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW(),
    -- retention
    retention_days INTEGER     NOT NULL DEFAULT 60,
    retain_reason  VARCHAR(500),
    expires_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_cell_notes_created_at  ON cell_notes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cell_notes_tags        ON cell_notes USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_cell_notes_expires_at  ON cell_notes(expires_at) WHERE expires_at IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_cell_notes_updated_at') THEN
        CREATE TRIGGER update_cell_notes_updated_at
            BEFORE UPDATE ON cell_notes
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
