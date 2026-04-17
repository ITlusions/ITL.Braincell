"""
BrainCell MCP Server - Lightweight HTTP implementation
"""

import logging
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from sqlalchemy import text

from src.core.config import get_settings
from src.core.database import SessionLocal, init_db
from src.models import DesignDecision, CodeSnippet, ArchitectureNote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BrainCell MCP", version="1.0.0")
init_db()


class MCPTools:
    """MCP tool implementations"""
    
    @staticmethod
    def search_memory(query: str, memory_type: str = None, limit: int = 10) -> dict:
        """Search memory by type"""
        db = SessionLocal()
        results = []
        q = query.lower()
        
        try:
            if not memory_type or memory_type == "decisions":
                results.extend([{
                    "id": str(d.id),
                    "type": "decision",
                    "decision": d.decision,
                    "rationale": d.rationale
                } for d in db.query(DesignDecision)
                    .filter(DesignDecision.decision.ilike(f"%{q}%"))
                    .limit(limit).all()])
            
            if not memory_type or memory_type == "snippets":
                results.extend([{
                    "id": str(s.id),
                    "type": "snippet",
                    "title": s.title,
                    "language": s.language
                } for s in db.query(CodeSnippet)
                    .filter(CodeSnippet.title.ilike(f"%{q}%"))
                    .limit(limit).all()])
            
            if not memory_type or memory_type == "architecture":
                results.extend([{
                    "id": str(a.id),
                    "type": "architecture",
                    "component": a.component,
                    "description": a.description[:100]
                } for a in db.query(ArchitectureNote)
                    .filter(ArchitectureNote.component.ilike(f"%{q}%"))
                    .limit(limit).all()])
        finally:
            db.close()
        
        return {"query": query, "count": len(results), "results": results}
    
    @staticmethod
    def save_decision(decision: str, rationale: str = None, impact: str = None) -> dict:
        """Save design decision"""
        db = SessionLocal()
        try:
            d = DesignDecision(decision=decision, rationale=rationale, impact=impact, status="active")
            db.add(d)
            db.commit()
            db.refresh(d)
            return {"success": True, "id": str(d.id)}
        finally:
            db.close()
    
    @staticmethod
    def save_snippet(title: str, code_content: str, language: str = None, description: str = None, tags: list = None) -> dict:
        """Save code snippet"""
        db = SessionLocal()
        try:
            s = CodeSnippet(title=title, code_content=code_content, language=language, description=description, tags=tags or [])
            db.add(s)
            db.commit()
            db.refresh(s)
            return {"success": True, "id": str(s.id)}
        finally:
            db.close()
    
    @staticmethod
    def save_architecture(component: str, description: str, note_type: str = "general", tags: list = None) -> dict:
        """Save architecture note"""
        db = SessionLocal()
        try:
            a = ArchitectureNote(component=component, description=description, type=note_type, tags=tags or [], status="active")
            db.add(a)
            db.commit()
            db.refresh(a)
            return {"success": True, "id": str(a.id)}
        finally:
            db.close()
    
    @staticmethod
    def list_memories(memory_type: str = None, limit: int = 50) -> dict:
        """List all memories"""
        db = SessionLocal()
        items = []
        try:
            if not memory_type or memory_type == "decisions":
                items.extend([{"id": str(d.id), "type": "decision", "title": d.decision[:50]}
                    for d in db.query(DesignDecision).limit(limit).all()])
            if not memory_type or memory_type == "snippets":
                items.extend([{"id": str(s.id), "type": "snippet", "title": s.title}
                    for s in db.query(CodeSnippet).limit(limit).all()])
            if not memory_type or memory_type == "architecture":
                items.extend([{"id": str(a.id), "type": "architecture", "title": a.component}
                    for a in db.query(ArchitectureNote).limit(limit).all()])
        finally:
            db.close()
        return {"count": len(items), "items": items}


TOOLS = {
    "search_memory": {
        "description": "Search memory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "memory_type": {"type": "string", "description": "Filter by type"},
                "limit": {"type": "integer", "description": "Result limit", "default": 10}
            },
            "required": ["query"]
        }
    },
    "save_decision": {
        "description": "Save design decision",
        "inputSchema": {
            "type": "object",
            "properties": {
                "decision": {"type": "string", "description": "Decision"},
                "rationale": {"type": "string", "description": "Rationale"},
                "impact": {"type": "string", "description": "Impact"}
            },
            "required": ["decision"]
        }
    },
    "save_code_snippet": {
        "description": "Save code snippet",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title"},
                "code_content": {"type": "string", "description": "Code"},
                "language": {"type": "string", "description": "Language"},
                "description": {"type": "string", "description": "Description"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"}
            },
            "required": ["title", "code_content"]
        }
    },
    "save_architecture_note": {
        "description": "Save architecture note",
        "inputSchema": {
            "type": "object",
            "properties": {
                "component": {"type": "string", "description": "Component"},
                "description": {"type": "string", "description": "Description"},
                "note_type": {"type": "string", "description": "Type"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"}
            },
            "required": ["component", "description"]
        }
    },
    "list_memories": {
        "description": "List memories",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_type": {"type": "string", "description": "Filter by type"},
                "limit": {"type": "integer", "description": "Limit", "default": 50}
            }
        }
    }
}


@app.post("/mcp")
async def mcp_handler(request: Request):
    """MCP JSON-RPC message handler"""
    try:
        msg = await request.json()
        method = msg.get("method")
        params = msg.get("params", {})
        msg_id = msg.get("id")
        
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "BrainCell", "version": "1.0.0"}
            }
        
        elif method == "tools/list":
            result = {"tools": [
                {"name": k, "description": v["description"], "inputSchema": v["inputSchema"]}
                for k, v in TOOLS.items()
            ]}
        
        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            
            if tool_name == "search_memory":
                result = MCPTools.search_memory(args.get("query"), args.get("memory_type"), args.get("limit", 10))
            elif tool_name == "save_decision":
                result = MCPTools.save_decision(args.get("decision"), args.get("rationale"), args.get("impact"))
            elif tool_name == "save_code_snippet":
                result = MCPTools.save_snippet(args.get("title"), args.get("code_content"), args.get("language"), args.get("description"), args.get("tags"))
            elif tool_name == "save_architecture_note":
                result = MCPTools.save_architecture(args.get("component"), args.get("description"), args.get("note_type"), args.get("tags"))
            elif tool_name == "list_memories":
                result = MCPTools.list_memories(args.get("memory_type"), args.get("limit", 50))
            else:
                return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": msg_id}
        
        else:
            return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": msg_id}
        
        return {"jsonrpc": "2.0", "result": result, "id": msg_id}
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": msg.get("id") if 'msg' in locals() else None}


@app.get("/tools")
async def list_tools():
    """REST tool discovery (legacy)"""
    return {"tools": [
        {"name": k, "description": v["description"], "inputSchema": v["inputSchema"]}
        for k, v in TOOLS.items()
    ]}


@app.get("/health")
async def health():
    """Health check"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "service": "braincell-mcp"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}, 503


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9506, log_level="info")
