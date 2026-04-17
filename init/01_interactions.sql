-- Interactions / messages

CREATE TABLE IF NOT EXISTS interactions (
    id               UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id  UUID          NOT NULL,
    session_id       UUID          NOT NULL,
    role             VARCHAR(50)   NOT NULL,
    content          TEXT          NOT NULL,
    message_type     VARCHAR(50)   DEFAULT 'message',
    tokens_used      INTEGER       DEFAULT 0,
    timestamp        TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    created_at       TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    meta_data        JSONB         DEFAULT '{}'::jsonb,
    -- retention
    retention_days   INTEGER       NOT NULL DEFAULT 30,
    retain_reason    VARCHAR(500),
    expires_at       TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_interactions_conversation_id ON interactions(conversation_id);
CREATE INDEX IF NOT EXISTS idx_interactions_session_id      ON interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_interactions_role            ON interactions(role);
CREATE INDEX IF NOT EXISTS idx_interactions_timestamp       ON interactions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_message_type    ON interactions(message_type);
CREATE INDEX IF NOT EXISTS idx_interactions_content         ON interactions USING GIN(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_interactions_expires_at      ON interactions(expires_at) WHERE expires_at IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_interactions_updated_at') THEN
        CREATE TRIGGER update_interactions_updated_at
            BEFORE UPDATE ON interactions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;
