"""Core schemas — shared types only.
Entity schemas have moved to src/cells/<name>/schema.py.
"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


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
