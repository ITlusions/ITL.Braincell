-- Initialize BrainCell database schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "jsonb_utils";

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    topic TEXT NOT NULL,
    summary TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_timestamp ON conversations(timestamp DESC);
CREATE INDEX idx_conversations_topic ON conversations USING GIN(to_tsvector('english', topic));

-- Interactions/Messages table
CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL,
    session_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'message',
    tokens_used INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    meta_data JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_interactions_conversation_id ON interactions(conversation_id);
CREATE INDEX idx_interactions_session_id ON interactions(session_id);
CREATE INDEX idx_interactions_role ON interactions(role);
CREATE INDEX idx_interactions_timestamp ON interactions(timestamp DESC);
CREATE INDEX idx_interactions_message_type ON interactions(message_type);
CREATE INDEX idx_interactions_content ON interactions USING GIN(to_tsvector('english', content));

-- Design decisions table
CREATE TABLE design_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision TEXT NOT NULL,
    rationale TEXT,
    impact TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'superseded')),
    date_made TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_decisions_status ON design_decisions(status);
CREATE INDEX idx_decisions_date ON design_decisions(date_made DESC);
CREATE INDEX idx_decisions_decision ON design_decisions USING GIN(to_tsvector('english', decision));

-- Architecture notes table
CREATE TABLE architecture_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component TEXT NOT NULL,
    description TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'general' CHECK (type IN ('general', 'pattern', 'integration', 'constraint')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'draft')),
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_arch_notes_component ON architecture_notes(component);
CREATE INDEX idx_arch_notes_type ON architecture_notes(type);
CREATE INDEX idx_arch_notes_tags ON architecture_notes USING GIN(tags);

-- Files discussed table
CREATE TABLE files_discussed (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path TEXT NOT NULL UNIQUE,
    description TEXT,
    language VARCHAR(50),
    purpose TEXT,
    last_modified TIMESTAMP,
    discussion_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_files_path ON files_discussed(file_path);
CREATE INDEX idx_files_language ON files_discussed(language);
CREATE INDEX idx_files_discussion_count ON files_discussed(discussion_count DESC);

-- Code snippets table (JSON documents)
CREATE TABLE code_snippets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    code_content TEXT NOT NULL,
    language VARCHAR(50),
    file_path TEXT,
    line_start INTEGER,
    line_end INTEGER,
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_snippets_language ON code_snippets(language);
CREATE INDEX idx_snippets_file ON code_snippets(file_path);
CREATE INDEX idx_snippets_tags ON code_snippets USING GIN(tags);

-- Context snapshots table (JSON documents)
CREATE TABLE context_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_name TEXT NOT NULL,
    context_data JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_snapshots_name ON context_snapshots(snapshot_name);
CREATE INDEX idx_snapshots_timestamp ON context_snapshots(timestamp DESC);

-- Memory session tracking
CREATE TABLE memory_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_name TEXT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
    conversation_ids UUID[] DEFAULT '{}',
    file_ids UUID[] DEFAULT '{}',
    summary TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_sessions_status ON memory_sessions(status);
CREATE INDEX idx_sessions_start_time ON memory_sessions(start_time DESC);
CREATE INDEX idx_sessions_end_time ON memory_sessions(end_time DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to all tables with updated_at
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_interactions_updated_at BEFORE UPDATE ON interactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_decisions_updated_at BEFORE UPDATE ON design_decisions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_arch_notes_updated_at BEFORE UPDATE ON architecture_notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_files_updated_at BEFORE UPDATE ON files_discussed
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_snippets_updated_at BEFORE UPDATE ON code_snippets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_snapshots_updated_at BEFORE UPDATE ON context_snapshots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON memory_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
