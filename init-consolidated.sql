-- Extensions and shared functions

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "jsonb_utils";

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
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
-- Research questions cell
-- Tracks end-user questions that require research follow-up.
-- Status lifecycle: pending â†’ investigating â†’ answered â†’ closed

CREATE TABLE IF NOT EXISTS cell_research_questions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question        TEXT        NOT NULL,
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority        VARCHAR(20) NOT NULL DEFAULT 'medium',
    context         TEXT,
    answer          TEXT,
    source          VARCHAR(50) NOT NULL DEFAULT 'auto_detected',
    source_interaction_id UUID,
    tags            TEXT[]      NOT NULL DEFAULT '{}',
    meta_data       JSONB       NOT NULL DEFAULT '{}',
    retention_days  INTEGER,
    retain_reason   TEXT,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rq_status   ON cell_research_questions (status);
CREATE INDEX IF NOT EXISTS idx_rq_priority ON cell_research_questions (priority);
CREATE INDEX IF NOT EXISTS idx_rq_src_iid  ON cell_research_questions (source_interaction_id);
CREATE INDEX IF NOT EXISTS idx_rq_expires  ON cell_research_questions (expires_at)
    WHERE expires_at IS NOT NULL;
