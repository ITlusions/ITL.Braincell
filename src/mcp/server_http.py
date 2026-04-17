"""
BrainCell MCP Server - FastMCP with Streamable HTTP Protocol

Uses the official Model Context Protocol library with Streamable HTTP transport
for production-grade remote MCP server capability. Supports bidirectional
communication via HTTP POST (client→server) and GET/SSE (server→client).

Features:
- FastMCP with @mcp.tool() decorators for clean tool definition
- Streamable HTTP protocol for remote/production deployment
- Stateless mode for horizontal scalability
- Compatible with MCP Inspector and Claude Desktop
- SQL database for persistent memory storage
- Minimal dependencies for efficient deployment
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
import uvicorn

from src.core.config import get_settings
from src.core.database import SessionLocal, init_db
from src.core.models import (
    DesignDecision, CodeSnippet, ArchitectureNote
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize database
init_db()

# Initialize FastMCP with stateless HTTP mode for production scalability
# stateless_http=True enables each replica to handle requests independently
# without requiring session affinity or shared state
mcp = FastMCP("braincell", stateless_http=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tool Implementations - Using @mcp.tool() decorators
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def search_memory(
    query: str,
    memory_type: str | None = None,
    limit: int = 10
) -> dict:
    """
    Semantic search across all memory using natural language.
    
    Searches through design decisions, code snippets, and architecture notes
    to find relevant information based on the provided query.
    """
    try:
        if not query:
            return {"error": "query is required"}
        
        db = SessionLocal()
        results = []
        query_lower = query.lower()
        
        try:
            # Search in design decisions
            if memory_type in ["decisions", None]:
                decisions = db.query(DesignDecision)\
                    .filter(DesignDecision.decision.ilike(f"%{query_lower}%"))\
                    .limit(limit).all()
                results.extend([{
                    "id": str(d.id),
                    "type": "decision",
                    "decision": str(d.decision) if d.decision else None,
                    "rationale": str(d.rationale) if d.rationale else None
                } for d in decisions])
            
            # Search in code snippets
            if memory_type in ["snippets", None]:
                snippets = db.query(CodeSnippet)\
                    .filter(CodeSnippet.title.ilike(f"%{query_lower}%") | 
                            CodeSnippet.description.ilike(f"%{query_lower}%"))\
                    .limit(limit).all()
                results.extend([{
                    "id": str(s.id),
                    "type": "snippet",
                    "title": str(s.title) if s.title else None,
                    "language": str(s.language) if s.language else None,
                    "description": str(s.description) if s.description else None
                } for s in snippets])
            
            # Search in architecture notes
            if memory_type in ["architecture", None]:
                arch_notes = db.query(ArchitectureNote)\
                    .filter(ArchitectureNote.component.ilike(f"%{query_lower}%") |
                            ArchitectureNote.description.ilike(f"%{query_lower}%"))\
                    .limit(limit).all()
                results.extend([{
                    "id": str(a.id),
                    "type": "architecture",
                    "component": str(a.component) if a.component else None,
                    "description": str(a.description) if a.description else None
                } for a in arch_notes])
            
            return {
                "query": str(query),
                "count": len(results),
                "results": results
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
async def get_relevant_context(
    query: str,
    limit: int = 5
) -> dict:
    """
    Get relevant context for a task from memory.
    
    Performs semantic search to find related decisions and provides recent
    active design decisions that might inform the current task.
    """
    try:
        if not query:
            return {"error": "query is required"}
        
        db = SessionLocal()
        
        try:
            query_lower = query.lower()
            
            # Get semantic results by searching decisions and snippets
            search_results = []
            
            decisions = db.query(DesignDecision)\
                .filter(DesignDecision.decision.ilike(f"%{query_lower}%"))\
                .limit(limit).all()
            search_results.extend([{
                "id": str(d.id),
                "type": "decision",
                "decision": str(d.decision)[:200] if d.decision else None,
                "rationale": str(d.rationale)[:200] if d.rationale else None
            } for d in decisions])
            
            # Get recent active decisions
            recent_decisions = db.query(DesignDecision)\
                .filter(DesignDecision.status == "active")\
                .order_by(DesignDecision.date_made.desc())\
                .limit(3).all()
            
            return {
                "query": str(query),
                "semantic_results": search_results,
                "recent_decisions": [{
                    "decision": str(d.decision) if d.decision else None,
                    "rationale": str(d.rationale) if d.rationale else None,
                    "date": (d.date_made.isoformat() if isinstance(d.date_made, datetime) else str(d.date_made)) if d.date_made else None
                } for d in recent_decisions]
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Get context failed: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
async def save_decision(
    decision: str,
    rationale: str | None = None,
    impact: str | None = None
) -> dict:
    """
    Save a design decision to memory for future reference.
    
    Stores architectural decisions with their rationale and expected impact
    for later retrieval and learning.
    """
    try:
        if not decision:
            return {"error": "decision is required"}
        
        db = SessionLocal()
        
        try:
            design_decision = DesignDecision(
                decision=str(decision),
                rationale=str(rationale) if rationale else None,
                impact=str(impact) if impact else None,
                status="active"
            )
            
            db.add(design_decision)
            db.commit()
            db.refresh(design_decision)
            
            return {
                "success": True,
                "id": str(design_decision.id),
                "decision": str(decision)
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Save decision failed: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
async def save_code_snippet(
    title: str,
    code_content: str,
    language: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None
) -> dict:
    """
    Save a reusable code pattern to memory.
    
    Stores code snippets with metadata for easy retrieval and reuse across
    projects. Supports tagging for better organization.
    """
    try:
        if not title or not code_content:
            return {"error": "title and code_content are required"}
        
        db = SessionLocal()
        
        try:
            snippet = CodeSnippet(
                title=str(title),
                code_content=str(code_content),
                language=str(language) if language else None,
                description=str(description) if description else None,
                tags=[str(t) for t in (tags if isinstance(tags, (list, tuple)) else [])]
            )
            
            db.add(snippet)
            db.commit()
            db.refresh(snippet)
            
            return {
                "success": True,
                "id": str(snippet.id),
                "title": str(title)
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Save snippet failed: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
async def save_architecture_note(
    component: str,
    description: str,
    note_type: str | None = None,
    tags: list[str] | None = None
) -> dict:
    """
    Save architecture or design notes to memory.
    
    Documents component designs, patterns, and architectural decisions
    for reference and knowledge sharing.
    """
    try:
        if not component or not description:
            return {"error": "component and description are required"}
        
        db = SessionLocal()
        
        try:
            arch_note = ArchitectureNote(
                component=str(component),
                description=str(description),
                type=str(note_type) if note_type else "general",
                tags=[str(t) for t in (tags if isinstance(tags, (list, tuple)) else [])],
                status="active"
            )
            
            db.add(arch_note)
            db.commit()
            db.refresh(arch_note)
            
            return {
                "success": True,
                "id": str(arch_note.id),
                "component": str(component)
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Save architecture note failed: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
async def list_memories(
    memory_type: str | None = None,
    limit: int = 50
) -> dict:
    """
    List stored memories by type.
    
    Retrieves all stored memories (decisions, code snippets, architecture notes)
    with optional filtering by type.
    """
    try:
        db = SessionLocal()
        results = []
        
        try:
            if memory_type in ["decisions", None]:
                decisions = db.query(DesignDecision)\
                    .order_by(DesignDecision.date_made.desc())\
                    .limit(limit).all()
                results.extend([{
                    "id": str(d.id),
                    "type": "decision",
                    "decision": str(d.decision)[:100] if d.decision else None,
                    "status": str(d.status) if d.status else "unknown"
                } for d in decisions])
            
            if memory_type in ["snippets", None]:
                snippets = db.query(CodeSnippet)\
                    .order_by(CodeSnippet.created_at.desc())\
                    .limit(limit).all()
                results.extend([{
                    "id": str(s.id),
                    "type": "snippet",
                    "title": str(s.title) if s.title else None,
                    "language": str(s.language) if s.language else None,
                    "tags": [str(t) for t in (s.tags if isinstance(s.tags, (list, tuple)) and s.tags else [])]
                } for s in snippets])
            
            if memory_type in ["architecture", None]:
                arch_notes = db.query(ArchitectureNote)\
                    .order_by(ArchitectureNote.component)\
                    .limit(limit).all()
                results.extend([{
                    "id": str(a.id),
                    "type": "architecture",
                    "component": str(a.component) if a.component else None,
                    "description": str(a.description)[:100] if a.description else None
                } for a in arch_notes])
            
            return {
                "count": len(results),
                "items": results
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"List memories failed: {e}", exc_info=True)
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Application Setup with Streamable HTTP MCP Protocol
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown of the FastAPI application, including
    mounting the FastMCP Streamable HTTP endpoint and managing the session
    manager lifecycle.
    """
    # Startup
    logger.info("Starting BrainCell MCP Server with Streamable HTTP protocol")
    
    # Mount the MCP Streamable HTTP endpoint
    # This creates the /mcp endpoint that handles both JSON-RPC POST requests
    # and SSE GET streams for bidirectional communication
    app.mount("/", mcp.streamable_http_app())
    
    # Enter the session manager context for handling concurrent sessions
    async with mcp.session_manager.run():
        yield
    
    # Shutdown
    logger.info("Shutting down BrainCell MCP Server")


# Create FastAPI application with Streamable HTTP MCP protocol
app = FastAPI(
    title="BrainCell MCP Server",
    description="FastMCP server with Streamable HTTP transport for production deployment",
    version="2.0.0",
    lifespan=lifespan
)


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint for monitoring and load balancers."""
    try:
        # Check database connectivity
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "service": "braincell-mcp",
            "protocol": "streamable-http",
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    # Run the FastAPI application with Uvicorn
    # The MCP Streamable HTTP endpoint will be available at /mcp
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9506,
        log_level="info"
    )

