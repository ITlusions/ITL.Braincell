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
from src.cells.decisions.model import DesignDecision
from src.cells.snippets.model import CodeSnippet
from src.cells.architecture_notes.model import ArchitectureNote

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

# Auto-register per-cell MCP tools via the MemoryCell plugin system.
# Any cell that implements register_mcp_tools() is discovered and registered
# here — adding a new cell automatically exposes its tools without touching
# this file.
from src.cells import discover_cells as _discover_cells

for _cell in _discover_cells():
    _cell.register_mcp_tools(mcp)


# ─────────────────────────────────────────────────────────────────────────────
# Cross-cell aggregate tools (span multiple cells)
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

