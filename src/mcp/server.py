"""
BrainCell MCP Server - Exposes persistent memory functionality via Model Context Protocol

This server allows agents with MCP support to interact with BrainCell's memory system,
including semantic search, storage, and retrieval of:
- Conversations
- Design Decisions
- Architecture Notes
- Code Snippets
- Context Snapshots
"""

import json
import logging
from typing import Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import SessionLocal, init_db
from src.models import (
    Conversation, DesignDecision, ArchitectureNote,
    CodeSnippet, ContextSnapshot, FileDiscussed, MemorySession
)
from src.schemas import (
    ConversationCreate, DecisionCreate, ArchitectureNoteCreate,
    CodeSnippetCreate, ContextSnapshotCreate, FileDiscussedCreate
)
from src.weaviate_service import get_weaviate_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize FastAPI app for MCP server
mcp_app = FastAPI(
    title="BrainCell MCP Server",
    description="Memory Context Protocol server for BrainCell persistent memory",
    version="1.0.0"
)

# MCP Tool Response Schema
class ToolResult(BaseModel):
    """Standard tool result format for MCP"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    message: Optional[str] = None


class Tool(BaseModel):
    """Tool definition"""
    name: str
    description: str
    input_schema: dict


# ============================================================================
# MCP Tool: Search Memory
# ============================================================================

@mcp_app.post("/tools/search_memory")
async def search_memory(
    query: str,
    memory_type: Optional[str] = None,  # conversations, decisions, architecture, snippets, etc.
    limit: int = 10,
    threshold: float = 0.6
) -> ToolResult:
    """
    Search across all memory using semantic search via Weaviate
    
    Args:
        query: Natural language search query
        memory_type: Optional filter by memory type
        limit: Maximum results to return
        threshold: Minimum relevance threshold (0-1)
    """
    try:
        weaviate = get_weaviate_service()
        results = weaviate.semantic_search(query, limit, memory_type)
        
        return ToolResult(
            success=True,
            data={
                "query": query,
                "count": len(results),
                "results": results,
                "threshold": threshold
            },
            message=f"Found {len(results)} relevant memories"
        )
    except Exception as e:
        logger.error(f"Search memory failed: {str(e)}")
        return ToolResult(
            success=False,
            error=str(e),
            message="Failed to search memory"
        )


# ============================================================================
# MCP Tool: Save Conversation
# ============================================================================

@mcp_app.post("/tools/save_conversation")
async def save_conversation(
    session_id: str,
    topic: str,
    summary: Optional[str] = None,
    metadata: Optional[dict] = None
) -> ToolResult:
    """
    Save a conversation to memory
    
    Args:
        session_id: Session identifier (UUID format)
        topic: Conversation topic/title
        summary: Optional conversation summary
        metadata: Additional metadata
    """
    try:
        db = SessionLocal()
        
        # Convert session_id string to UUID if needed
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            session_uuid = uuid4()
        
        conversation = Conversation(
            session_id=session_uuid,
            topic=topic,
            summary=summary,
            meta_data=metadata or {}
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        # Index in Weaviate for semantic search
        weaviate = get_weaviate_service()
        weaviate.index_conversation(
            str(conversation.id),
            topic,
            summary or topic
        )
        
        db.close()
        
        return ToolResult(
            success=True,
            data={
                "id": str(conversation.id),
                "session_id": str(conversation.session_id),
                "topic": topic,
                "timestamp": conversation.timestamp.isoformat()
            },
            message=f"Conversation saved: {conversation.id}"
        )
    except Exception as e:
        logger.error(f"Save conversation failed: {str(e)}")
        return ToolResult(
            success=False,
            error=str(e),
            message="Failed to save conversation"
        )


# ============================================================================
# MCP Tool: Save Design Decision
# ============================================================================

@mcp_app.post("/tools/save_decision")
async def save_decision(
    decision: str,
    rationale: Optional[str] = None,
    impact: Optional[str] = None,
    status: str = "active",
    metadata: Optional[dict] = None
) -> ToolResult:
    """
    Save a design decision to memory
    
    Args:
        decision: The decision text
        rationale: Why this decision was made
        impact: Impact of this decision
        status: Decision status (active, archived, superseded)
        metadata: Additional metadata
    """
    try:
        db = SessionLocal()
        
        design_decision = DesignDecision(
            decision=decision,
            rationale=rationale,
            impact=impact,
            status=status,
            meta_data=metadata or {}
        )
        
        db.add(design_decision)
        db.commit()
        db.refresh(design_decision)
        
        # Index in Weaviate
        weaviate = get_weaviate_service()
        weaviate.index_decision(
            str(design_decision.id),
            decision,
            rationale or decision
        )
        
        db.close()
        
        return ToolResult(
            success=True,
            data={
                "id": str(design_decision.id),
                "decision": decision,
                "status": status,
                "date_made": design_decision.date_made.isoformat()
            },
            message=f"Decision saved: {design_decision.id}"
        )
    except Exception as e:
        logger.error(f"Save decision failed: {str(e)}")
        return ToolResult(
            success=False,
            error=str(e),
            message="Failed to save decision"
        )


# ============================================================================
# MCP Tool: Save Architecture Note
# ============================================================================

@mcp_app.post("/tools/save_architecture_note")
async def save_architecture_note(
    component: str,
    description: str,
    note_type: str = "general",
    status: str = "active",
    tags: Optional[List[str]] = None,
    metadata: Optional[dict] = None
) -> ToolResult:
    """
    Save architecture notes to memory
    
    Args:
        component: Component name
        description: Detailed description
        note_type: Type of note (general, design, pattern, etc.)
        status: Note status (active, archived)
        tags: List of tags for organization
        metadata: Additional metadata
    """
    try:
        db = SessionLocal()
        
        arch_note = ArchitectureNote(
            component=component,
            description=description,
            type=note_type,
            status=status,
            tags=tags or [],
            meta_data=metadata or {}
        )
        
        db.add(arch_note)
        db.commit()
        db.refresh(arch_note)
        
        # Index in Weaviate
        weaviate = get_weaviate_service()
        weaviate.index_architecture_note(
            str(arch_note.id),
            component,
            description
        )
        
        db.close()
        
        return ToolResult(
            success=True,
            data={
                "id": str(arch_note.id),
                "component": component,
                "type": note_type,
                "tags": tags or []
            },
            message=f"Architecture note saved: {arch_note.id}"
        )
    except Exception as e:
        logger.error(f"Save architecture note failed: {str(e)}")
        return ToolResult(
            success=False,
            error=str(e),
            message="Failed to save architecture note"
        )


# ============================================================================
# MCP Tool: Save Code Snippet
# ============================================================================

@mcp_app.post("/tools/save_code_snippet")
async def save_code_snippet(
    title: str,
    code_content: str,
    language: Optional[str] = None,
    file_path: Optional[str] = None,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[dict] = None
) -> ToolResult:
    """
    Save code snippets to memory for future reference
    
    Args:
        title: Snippet title
        code_content: The actual code
        language: Programming language
        file_path: Original file path
        line_start: Starting line number
        line_end: Ending line number
        description: What this snippet does
        tags: Categorization tags
        metadata: Additional metadata
    """
    try:
        db = SessionLocal()
        
        snippet = CodeSnippet(
            title=title,
            code_content=code_content,
            language=language,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            description=description,
            tags=tags or [],
            meta_data=metadata or {}
        )
        
        db.add(snippet)
        db.commit()
        db.refresh(snippet)
        
        # Index in Weaviate
        weaviate = get_weaviate_service()
        weaviate.index_code_snippet(
            str(snippet.id),
            title,
            code_content,
            description or title
        )
        
        db.close()
        
        return ToolResult(
            success=True,
            data={
                "id": str(snippet.id),
                "title": title,
                "language": language,
                "file_path": file_path,
                "tags": tags or []
            },
            message=f"Code snippet saved: {snippet.id}"
        )
    except Exception as e:
        logger.error(f"Save code snippet failed: {str(e)}")
        return ToolResult(
            success=False,
            error=str(e),
            message="Failed to save code snippet"
        )


# ============================================================================
# MCP Tool: Save Context Snapshot
# ============================================================================

@mcp_app.post("/tools/save_context_snapshot")
async def save_context_snapshot(
    snapshot_name: str,
    context_data: dict,
    metadata: Optional[dict] = None
) -> ToolResult:
    """
    Save a complete context snapshot for later retrieval
    
    Args:
        snapshot_name: Name/identifier for the snapshot
        context_data: The full context data as JSON
        metadata: Additional metadata
    """
    try:
        db = SessionLocal()
        
        snapshot = ContextSnapshot(
            snapshot_name=snapshot_name,
            context_data=context_data,
            meta_data=metadata or {}
        )
        
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        
        db.close()
        
        return ToolResult(
            success=True,
            data={
                "id": str(snapshot.id),
                "name": snapshot_name,
                "timestamp": snapshot.timestamp.isoformat(),
                "data_keys": list(context_data.keys())
            },
            message=f"Context snapshot saved: {snapshot.id}"
        )
    except Exception as e:
        logger.error(f"Save context snapshot failed: {str(e)}")
        return ToolResult(
            success=False,
            error=str(e),
            message="Failed to save context snapshot"
        )


# ============================================================================
# MCP Tool: Retrieve Memory Item
# ============================================================================

@mcp_app.get("/tools/retrieve_memory/{item_id}")
async def retrieve_memory(
    item_id: str,
    item_type: Optional[str] = None
) -> ToolResult:
    """
    Retrieve a specific memory item by ID
    
    Args:
        item_id: UUID of the memory item
        item_type: Type of item (conversation, decision, etc.)
    """
    try:
        db = SessionLocal()
        item_uuid = UUID(item_id)
        
        # Try to find in each type if not specified
        if not item_type:
            conversation = db.query(Conversation).filter(Conversation.id == item_uuid).first()
            if conversation:
                result = {
                    "id": str(conversation.id),
                    "type": "conversation",
                    "topic": conversation.topic,
                    "summary": conversation.summary,
                    "timestamp": conversation.timestamp.isoformat(),
                    "metadata": conversation.meta_data
                }
                db.close()
                return ToolResult(success=True, data=result)
            
            decision = db.query(DesignDecision).filter(DesignDecision.id == item_uuid).first()
            if decision:
                result = {
                    "id": str(decision.id),
                    "type": "decision",
                    "decision": decision.decision,
                    "rationale": decision.rationale,
                    "status": decision.status,
                    "date_made": decision.date_made.isoformat(),
                    "metadata": decision.meta_data
                }
                db.close()
                return ToolResult(success=True, data=result)
            
            snippet = db.query(CodeSnippet).filter(CodeSnippet.id == item_uuid).first()
            if snippet:
                result = {
                    "id": str(snippet.id),
                    "type": "code_snippet",
                    "title": snippet.title,
                    "language": snippet.language,
                    "code": snippet.code_content,
                    "description": snippet.description,
                    "tags": snippet.tags,
                    "metadata": snippet.meta_data
                }
                db.close()
                return ToolResult(success=True, data=result)
        
        db.close()
        return ToolResult(
            success=False,
            error=f"Memory item not found: {item_id}",
            message="Item not found"
        )
    except Exception as e:
        logger.error(f"Retrieve memory failed: {str(e)}")
        return ToolResult(
            success=False,
            error=str(e),
            message="Failed to retrieve memory"
        )


# ============================================================================
# MCP Tool: List Memories
# ============================================================================

@mcp_app.get("/tools/list_memories")
async def list_memories(
    memory_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> ToolResult:
    """
    List stored memories of a specific type or all types
    
    Args:
        memory_type: Type to filter (conversations, decisions, snippets, etc.)
        limit: Maximum items to return
        offset: Number of items to skip
    """
    try:
        db = SessionLocal()
        results = []
        
        if memory_type in ["conversations", None]:
            conversations = db.query(Conversation)\
                .order_by(Conversation.timestamp.desc())\
                .limit(limit).offset(offset).all()
            results.extend([{
                "id": str(c.id),
                "type": "conversation",
                "topic": c.topic,
                "timestamp": c.timestamp.isoformat()
            } for c in conversations])
        
        if memory_type in ["decisions", None]:
            decisions = db.query(DesignDecision)\
                .order_by(DesignDecision.date_made.desc())\
                .limit(limit).offset(offset).all()
            results.extend([{
                "id": str(d.id),
                "type": "decision",
                "decision": d.decision[:100],  # Truncate for list view
                "status": d.status,
                "date_made": d.date_made.isoformat()
            } for d in decisions])
        
        if memory_type in ["snippets", None]:
            snippets = db.query(CodeSnippet)\
                .order_by(CodeSnippet.created_at.desc())\
                .limit(limit).offset(offset).all()
            results.extend([{
                "id": str(s.id),
                "type": "code_snippet",
                "title": s.title,
                "language": s.language,
                "created_at": s.created_at.isoformat()
            } for s in snippets])
        
        if memory_type in ["architecture", None]:
            notes = db.query(ArchitectureNote)\
                .order_by(ArchitectureNote.created_at.desc())\
                .limit(limit).offset(offset).all()
            results.extend([{
                "id": str(n.id),
                "type": "architecture_note",
                "component": n.component,
                "type_": n.type,
                "status": n.status,
                "created_at": n.created_at.isoformat()
            } for n in notes])
        
        db.close()
        
        return ToolResult(
            success=True,
            data={
                "count": len(results),
                "items": results,
                "limit": limit,
                "offset": offset
            },
            message=f"Retrieved {len(results)} memory items"
        )
    except Exception as e:
        logger.error(f"List memories failed: {str(e)}")
        return ToolResult(
            success=False,
            error=str(e),
            message="Failed to list memories"
        )


# ============================================================================
# MCP Tool: Get Relevant Context
# ============================================================================

@mcp_app.post("/tools/get_relevant_context")
async def get_relevant_context(
    query: str,
    limit: int = 5
) -> ToolResult:
    """
    Get the most relevant context from memory for a given query
    Combines semantic search with structured data retrieval
    
    Args:
        query: The query or task description
        limit: Number of context items to return
    """
    try:
        weaviate = get_weaviate_service()
        db = SessionLocal()
        
        # Perform semantic search
        search_results = weaviate.semantic_search(query, limit)
        
        # Enrich with additional context from structured data
        context = {
            "query": query,
            "semantic_results": search_results,
            "recent_decisions": [],
            "recent_snippets": []
        }
        
        # Get recent decisions
        recent_decisions = db.query(DesignDecision)\
            .filter(DesignDecision.status == "active")\
            .order_by(DesignDecision.date_made.desc())\
            .limit(3).all()
        
        context["recent_decisions"] = [{
            "id": str(d.id),
            "decision": d.decision,
            "rationale": d.rationale
        } for d in recent_decisions]
        
        # Get relevant code snippets
        recent_snippets = db.query(CodeSnippet)\
            .order_by(CodeSnippet.created_at.desc())\
            .limit(3).all()
        
        context["recent_snippets"] = [{
            "id": str(s.id),
            "title": s.title,
            "language": s.language,
            "description": s.description
        } for s in recent_snippets]
        
        db.close()
        
        return ToolResult(
            success=True,
            data=context,
            message="Context retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Get relevant context failed: {str(e)}")
        return ToolResult(
            success=False,
            error=str(e),
            message="Failed to get relevant context"
        )


# ============================================================================
# Health and System Endpoints
# ============================================================================

@mcp_app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        weaviate = get_weaviate_service()
        weaviate_health = weaviate.health_check()
        
        return {
            "status": "healthy",
            "database": "connected",
            "weaviate": "connected" if weaviate_health else "disconnected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@mcp_app.get("/tools")
async def list_tools():
    """List available MCP tools"""
    return {
        "tools": [
            {
                "name": "search_memory",
                "description": "Semantic search across all memory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "memory_type": {"type": "string", "description": "Optional filter"},
                        "limit": {"type": "integer", "default": 10},
                        "threshold": {"type": "number", "default": 0.6}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "save_conversation",
                "description": "Save a conversation to memory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "topic": {"type": "string"},
                        "summary": {"type": "string"},
                        "metadata": {"type": "object"}
                    },
                    "required": ["session_id", "topic"]
                }
            },
            {
                "name": "save_decision",
                "description": "Save a design decision",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "decision": {"type": "string"},
                        "rationale": {"type": "string"},
                        "impact": {"type": "string"},
                        "status": {"type": "string"}
                    },
                    "required": ["decision"]
                }
            },
            {
                "name": "save_architecture_note",
                "description": "Save architecture notes",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "component": {"type": "string"},
                        "description": {"type": "string"},
                        "note_type": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["component", "description"]
                }
            },
            {
                "name": "save_code_snippet",
                "description": "Save code snippets for reference",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "code_content": {"type": "string"},
                        "language": {"type": "string"},
                        "description": {"type": "string"},
                        "tags": {"type": "array"}
                    },
                    "required": ["title", "code_content"]
                }
            },
            {
                "name": "save_context_snapshot",
                "description": "Save context snapshots",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "snapshot_name": {"type": "string"},
                        "context_data": {"type": "object"}
                    },
                    "required": ["snapshot_name", "context_data"]
                }
            },
            {
                "name": "retrieve_memory",
                "description": "Retrieve a specific memory item",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string"},
                        "item_type": {"type": "string"}
                    },
                    "required": ["item_id"]
                }
            },
            {
                "name": "list_memories",
                "description": "List stored memories",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "memory_type": {"type": "string"},
                        "limit": {"type": "integer", "default": 50},
                        "offset": {"type": "integer", "default": 0}
                    }
                }
            },
            {
                "name": "get_relevant_context",
                "description": "Get relevant context for a query",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            }
        ]
    }


if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Start MCP server
    logger.info("Starting BrainCell MCP Server...")
    uvicorn.run(
        mcp_app,
        host="0.0.0.0",
        port=9506,
        log_level="info"
    )
