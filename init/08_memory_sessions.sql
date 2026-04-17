-- Memory sessions

CREATE TABLE IF NOT EXISTS memory_sessions (
    id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_name     TEXT        NOT NULL,
    start_time       TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    end_time         TIMESTAMP,
    status           VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
    conversation_ids UUID[]      DEFAULT '{}',
    file_ids         UUID[]      DEFAULT '{}',
    summary          TEXT,
    metadata         JSONB       DEFAULT '{}'::jsonb,
    -- retention
    retention_days   INTEGER     NOT NULL DEFAULT 90,
    retain_reason    VARCHAR(500),
    expires_at       TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sessions_status      ON memory_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time  ON memory_sessions(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_end_time    ON memory_sessions(end_time DESC);
CREATE INDEX IF NOT EXISTS idx_memory_sessions_expires_at ON memory_sessions(expires_at) WHERE expires_at IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_sessions_updated_at') THEN
        CREATE TRIGGER update_sessions_updated_at
            BEFORE UPDATE ON memory_sessions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
