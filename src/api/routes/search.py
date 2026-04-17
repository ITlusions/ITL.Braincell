"""Semantic Search routes - universal vector-based search across all entity types"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.schemas import SearchQuery, SearchResult
from src.services.weaviate_service import get_weaviate_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/conversations", response_model=list[SearchResult])
async def search_conversations(
    query: SearchQuery,
    db: Session = Depends(get_db),
):
    """Search conversations using semantic similarity"""
    weaviate = get_weaviate_service()
    results = weaviate.search_conversations(query.query, query.limit)
    
    return [
        SearchResult(
            id=UUID(r.get("embedding_id", "")),
            type="conversation",
            title=r.get("topic", ""),
            content=r.get("summary", ""),
            similarity_score=1 - r.get("_additional", {}).get("distance", 1),
            metadata={"session_id": r.get("session_id", "")}
        )
        for r in results if r.get("embedding_id")
    ]


@router.post("/decisions", response_model=list[SearchResult])
async def search_decisions(
    query: SearchQuery,
    db: Session = Depends(get_db),
):
    """Search design decisions using semantic similarity"""
    weaviate = get_weaviate_service()
    results = weaviate.search_decisions(query.query, query.limit)
    
    return [
        SearchResult(
            id=UUID(r.get("embedding_id", "")),
            type="decision",
            title="Design Decision",
            content=r.get("decision", ""),
            similarity_score=1 - r.get("_additional", {}).get("distance", 1),
            metadata={"rationale": r.get("rationale", "")}
        )
        for r in results if r.get("embedding_id")
    ]


@router.post("/code", response_model=list[SearchResult])
async def search_code(
    query: SearchQuery,
    db: Session = Depends(get_db),
):
    """Search code snippets using semantic similarity"""
    weaviate = get_weaviate_service()
    results = weaviate.search_code(query.query, query.limit)
    
    return [
        SearchResult(
            id=UUID(r.get("embedding_id", "")),
            type="code",
            title=r.get("title", ""),
            content=r.get("code_content", ""),
            similarity_score=1 - r.get("_additional", {}).get("distance", 1),
            metadata={"language": r.get("language", "")}
        )
        for r in results if r.get("embedding_id")
    ]


@router.post("/interactions", response_model=list[SearchResult])
async def search_interactions(
    query: SearchQuery,
    db: Session = Depends(get_db),
):
    """Search interactions/messages using semantic similarity"""
    weaviate = get_weaviate_service()
    results = weaviate.search_interactions(query.query, query.limit)
    
    return [
        SearchResult(
            id=UUID(r.get("embedding_id", "")),
            type="interaction",
            title=r.get("role", "").capitalize(),
            content=r.get("content", ""),
            similarity_score=1 - r.get("_additional", {}).get("distance", 1),
            metadata={
                "role": r.get("role", ""),
                "message_type": r.get("message_type", ""),
                "conversation_id": r.get("conversation_id", ""),
                "session_id": r.get("session_id", "")
            }
        )
        for r in results if r.get("embedding_id")
    ]


@router.post("/architecture-notes", response_model=list[SearchResult])
async def search_architecture_notes(
    query: SearchQuery,
    db: Session = Depends(get_db),
):
    """Search architecture notes using semantic similarity"""
    weaviate = get_weaviate_service()
    results = weaviate.search_architecture_notes(query.query, query.limit)
    
    return [
        SearchResult(
            id=UUID(r.get("embedding_id", "")),
            type="architecture-note",
            title=r.get("component", ""),
            content=r.get("description", ""),
            similarity_score=1 - r.get("_additional", {}).get("distance", 1),
            metadata={
                "type": r.get("type", ""),
                "tags": r.get("tags", "")
            }
        )
        for r in results if r.get("embedding_id")
    ]


@router.post("/files", response_model=list[SearchResult])
async def search_files(
    query: SearchQuery,
    db: Session = Depends(get_db),
):
    """Search files discussed using semantic similarity"""
    weaviate = get_weaviate_service()
    results = weaviate.search_files(query.query, query.limit)
    
    return [
        SearchResult(
            id=UUID(r.get("embedding_id", "")),
            type="file",
            title=r.get("file_path", ""),
            content=r.get("description", ""),
            similarity_score=1 - r.get("_additional", {}).get("distance", 1),
            metadata={
                "language": r.get("language", ""),
                "purpose": r.get("purpose", "")
            }
        )
        for r in results if r.get("embedding_id")
    ]


@router.post("/sessions", response_model=list[SearchResult])
async def search_sessions(
    query: SearchQuery,
    db: Session = Depends(get_db),
):
    """Search memory sessions using semantic similarity"""
    weaviate = get_weaviate_service()
    results = weaviate.search_sessions(query.query, query.limit)
    
    return [
        SearchResult(
            id=UUID(r.get("embedding_id", "")),
            type="session",
            title=r.get("session_name", ""),
            content=r.get("summary", ""),
            similarity_score=1 - r.get("_additional", {}).get("distance", 1),
            metadata={
                "status": r.get("status", "")
            }
        )
        for r in results if r.get("embedding_id")
    ]
