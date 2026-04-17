from datetime import datetime
from typing import Optional
from uuid import UUID
import uuid

from sqlalchemy import Column, String, Text, DateTime, Integer, ARRAY, JSON, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    """Mixin for timestamp fields"""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=func.now(), nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class Conversation(TimestampMixin, Base):
    """Conversation records"""
    __tablename__ = "conversations"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    topic = Column(String(500), nullable=False)
    summary = Column(Text)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    meta_data = Column(JSON, default={})


class DesignDecision(TimestampMixin, Base):
    """Design decisions and architectural choices"""
    __tablename__ = "design_decisions"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision = Column(Text, nullable=False)
    rationale = Column(Text)
    impact = Column(Text)
    status = Column(String(20), default="active", nullable=False, index=True)
    date_made = Column(DateTime, default=func.now(), nullable=False, index=True)
    meta_data = Column(JSON, default={})


class ArchitectureNote(TimestampMixin, Base):
    """Architecture and design notes"""
    __tablename__ = "architecture_notes"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    type = Column(String(50), default="general", index=True)
    status = Column(String(20), default="active")
    tags = Column(ARRAY(String), default=[])
    meta_data = Column(JSON, default={})


class FileDiscussed(TimestampMixin, Base):
    """Files mentioned in conversations"""
    __tablename__ = "files_discussed"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = Column(String(1024), unique=True, nullable=False, index=True)
    description = Column(Text)
    language = Column(String(50), index=True)
    purpose = Column(Text)
    last_modified = Column(DateTime)
    discussion_count = Column(Integer, default=1, index=True)
    meta_data = Column(JSON, default={})


class CodeSnippet(TimestampMixin, Base):
    """Code snippets for reference"""
    __tablename__ = "code_snippets"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    code_content = Column(Text, nullable=False)
    language = Column(String(50), index=True)
    file_path = Column(String(1024), index=True)
    line_start = Column(Integer)
    line_end = Column(Integer)
    description = Column(Text)
    tags = Column(ARRAY(String), default=[])
    meta_data = Column(JSON, default={})


class ContextSnapshot(TimestampMixin, Base):
    """Full context snapshots (JSON documents)"""
    __tablename__ = "context_snapshots"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_name = Column(String(255), nullable=False, index=True)
    context_data = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    meta_data = Column(JSON, default={})


class Interaction(TimestampMixin, Base):
    """Individual interactions/messages within conversations"""
    __tablename__ = "interactions"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    role = Column(String(50), nullable=False, index=True)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="message", index=True)  # message, query, response, decision, note
    tokens_used = Column(Integer, default=0)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    meta_data = Column(JSON, default={})


class MemorySession(TimestampMixin, Base):
    """Session tracking for memory operations"""
    __tablename__ = "memory_sessions"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_name = Column(String(255), nullable=False)
    start_time = Column(DateTime, default=func.now(), nullable=False, index=True)
    end_time = Column(DateTime, nullable=True, index=True)
    status = Column(String(20), default="active", index=True)
    conversation_ids = Column(ARRAY(PG_UUID(as_uuid=True)), default=[])
    file_ids = Column(ARRAY(PG_UUID(as_uuid=True)), default=[])
    summary = Column(Text)
    meta_data = Column(JSON, default={})
