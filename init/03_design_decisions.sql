-- Design decisions

CREATE TABLE IF NOT EXISTS design_decisions (
    id             UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision       TEXT        NOT NULL,
    rationale      TEXT,
    impact         TEXT,
    status         VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'superseded')),
    date_made      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    created_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    metadata       JSONB       DEFAULT '{}'::jsonb,
    -- retention (0 = keep forever)
    retention_days INTEGER     NOT NULL DEFAULT 0,
    retain_reason  VARCHAR(500),
    expires_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_decisions_status         ON design_decisions(status);
CREATE INDEX IF NOT EXISTS idx_decisions_date           ON design_decisions(date_made DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_decision       ON design_decisions USING GIN(to_tsvector('english', decision));
CREATE INDEX IF NOT EXISTS idx_design_decisions_expires_at ON design_decisions(expires_at) WHERE expires_at IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_decisions_updated_at') THEN
        CREATE TRIGGER update_decisions_updated_at
            BEFORE UPDATE ON design_decisions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
