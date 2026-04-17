from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


# Conversation schemas
class ConversationCreate(BaseModel):
    session_id: UUID
    topic: str
    summary: Optional[str] = None
    meta_data: Optional[dict] = Field(default_factory=dict)


class ConversationUpdate(BaseModel):
    topic: Optional[str] = None
    summary: Optional[str] = None
    meta_data: Optional[dict] = None


class ConversationResponse(ConversationCreate):
    id: UUID
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Design Decision schemas
class DecisionCreate(BaseModel):
    decision: str
    rationale: Optional[str] = None
    impact: Optional[str] = None
    status: str = "active"
    meta_data: Optional[dict] = Field(default_factory=dict)


class DecisionResponse(DecisionCreate):
    id: UUID
    date_made: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Architecture Note schemas
class ArchitectureNoteCreate(BaseModel):
    component: str
    description: str
    type: str = "general"
    status: str = "active"
    tags: Optional[List[str]] = Field(default_factory=list)
    meta_data: Optional[dict] = Field(default_factory=dict)


class ArchitectureNoteResponse(ArchitectureNoteCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# File Discussed schemas
class FileDiscussedCreate(BaseModel):
    file_path: str
    description: Optional[str] = None
    language: Optional[str] = None
    purpose: Optional[str] = None
    meta_data: Optional[dict] = Field(default_factory=dict)


class FileDiscussedResponse(FileDiscussedCreate):
    id: UUID
    discussion_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Code Snippet schemas
class CodeSnippetCreate(BaseModel):
    title: str
    code_content: str
    language: Optional[str] = None
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    meta_data: Optional[dict] = Field(default_factory=dict)


class CodeSnippetResponse(CodeSnippetCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Context Snapshot schemas
class ContextSnapshotCreate(BaseModel):
    snapshot_name: str
    context_data: dict
    meta_data: Optional[dict] = Field(default_factory=dict)


class ContextSnapshotResponse(ContextSnapshotCreate):
    id: UUID
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Memory Session schemas
class MemorySessionCreate(BaseModel):
    session_name: str
    summary: Optional[str] = None
    meta_data: Optional[dict] = Field(default_factory=dict)


class MemorySessionUpdate(BaseModel):
    status: Optional[str] = None
    summary: Optional[str] = None
    meta_data: Optional[dict] = None


class MemorySessionResponse(MemorySessionCreate):
    id: UUID
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    conversation_ids: List[UUID]
    file_ids: List[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Interaction/Message schemas
class InteractionCreate(BaseModel):
    conversation_id: UUID
    session_id: UUID
    role: str  # 'user', 'assistant', 'system'
    content: str
    message_type: str = "message"  # 'message', 'query', 'response', 'decision', 'note'
    tokens_used: Optional[int] = 0
    meta_data: Optional[dict] = Field(default_factory=dict)


class InteractionUpdate(BaseModel):
    content: Optional[str] = None
    role: Optional[str] = None
    meta_data: Optional[dict] = None


class InteractionResponse(InteractionCreate):
    id: UUID
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Search schemas
class SearchQuery(BaseModel):
    query: str
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)


class SearchResult(BaseModel):
    id: UUID
    type: str  # 'conversation', 'decision', 'note', etc.
    title: str
    content: str
    similarity_score: Optional[float] = None
    meta_data: dict
