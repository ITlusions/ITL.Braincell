-- Context snapshots

CREATE TABLE IF NOT EXISTS context_snapshots (
    id            UUID      PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_name TEXT      NOT NULL,
    context_data  JSONB     NOT NULL,
    timestamp     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata      JSONB     DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_snapshots_name      ON context_snapshots(snapshot_name);
CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON context_snapshots(timestamp DESC);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_snapshots_updated_at') THEN
        CREATE TRIGGER update_snapshots_updated_at
            BEFORE UPDATE ON context_snapshots
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
