-- Conversations

CREATE TABLE IF NOT EXISTS conversations (
    id             UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id     UUID        NOT NULL,
    topic          TEXT        NOT NULL,
    summary        TEXT,
    timestamp      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    created_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    metadata       JSONB       DEFAULT '{}'::jsonb,
    -- retention
    retention_days INTEGER     NOT NULL DEFAULT 90,
    retain_reason  VARCHAR(500),
    expires_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_conversations_session_id  ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp   ON conversations(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_topic       ON conversations USING GIN(to_tsvector('english', topic));
CREATE INDEX IF NOT EXISTS idx_conversations_expires_at  ON conversations(expires_at) WHERE expires_at IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_conversations_updated_at') THEN
        CREATE TRIGGER update_conversations_updated_at
            BEFORE UPDATE ON conversations
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
