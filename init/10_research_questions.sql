-- Research questions cell
-- Tracks end-user questions that require research follow-up.
-- Status lifecycle: pending → investigating → answered → closed

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
