-- Architecture notes

CREATE TABLE IF NOT EXISTS architecture_notes (
    id             UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    component      TEXT        NOT NULL,
    description    TEXT        NOT NULL,
    type           VARCHAR(50) DEFAULT 'general' CHECK (type IN ('general', 'pattern', 'integration', 'constraint')),
    status         VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'draft')),
    tags           TEXT[]      DEFAULT '{}',
    created_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    metadata       JSONB       DEFAULT '{}'::jsonb,
    -- retention (0 = keep forever)
    retention_days INTEGER     NOT NULL DEFAULT 0,
    retain_reason  VARCHAR(500),
    expires_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_arch_notes_component       ON architecture_notes(component);
CREATE INDEX IF NOT EXISTS idx_arch_notes_type            ON architecture_notes(type);
CREATE INDEX IF NOT EXISTS idx_arch_notes_tags            ON architecture_notes USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_architecture_notes_expires_at ON architecture_notes(expires_at) WHERE expires_at IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_arch_notes_updated_at') THEN
        CREATE TRIGGER update_arch_notes_updated_at
            BEFORE UPDATE ON architecture_notes
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
