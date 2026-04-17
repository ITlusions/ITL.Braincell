"""
BrainCell MCP Server - Proper MCP Protocol Implementation

This implements the Model Context Protocol (MCP) to expose BrainCell's persistent memory
functionality to Claude and other MCP-compatible clients.
"""

import json
import logging
import sys
from typing import Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import SessionLocal, init_db
from src.models import (
    Conversation, DesignDecision, ArchitectureNote,
    CodeSnippet, ContextSnapshot, FileDiscussed, MemorySession
)
from src.weaviate_service import get_weaviate_service

# Configure logging to stderr (MCP uses stdout for protocol messages)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

settings = get_settings()


class MCPServer:
    """MCP Server implementation for BrainCell memory"""
    
    def __init__(self):
        """Initialize the MCP server"""
        self.tools = self._define_tools()
        init_db()
        logger.info("BrainCell MCP Server initialized")
    
    def _define_tools(self) -> dict:
        """Define available tools"""
        return {
            "search_memory": {
                "description": "Semantic search across all memory using natural language",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query"
                        },
                        "memory_type": {
                            "type": "string",
                            "description": "Optional: conversations, decisions, snippets, architecture"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "How many results to return (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            },
            "get_relevant_context": {
                "description": "Get relevant context for a task from memory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Task or question description"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "How many items to return",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            "save_decision": {
                "description": "Save a design decision to memory for future reference",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "decision": {
                            "type": "string",
                            "description": "The decision text"
                        },
                        "rationale": {
                            "type": "string",
                            "description": "Why this decision was made"
                        },
                        "impact": {
                            "type": "string",
                            "description": "Expected impact of this decision"
                        }
                    },
                    "required": ["decision"]
                }
            },
            "save_code_snippet": {
                "description": "Save a reusable code pattern to memory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Code snippet title"
                        },
                        "code_content": {
                            "type": "string",
                            "description": "The code itself"
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language"
                        },
                        "description": {
                            "type": "string",
                            "description": "What this code does"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for categorization"
                        }
                    },
                    "required": ["title", "code_content"]
                }
            },
            "save_architecture_note": {
                "description": "Save architecture or design notes to memory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component": {
                            "type": "string",
                            "description": "Component name"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description"
                        },
                        "note_type": {
                            "type": "string",
                            "description": "Type of note (general, design, pattern, etc.)"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for organization"
                        }
                    },
                    "required": ["component", "description"]
                }
            },
            "list_memories": {
                "description": "List stored memories by type",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "memory_type": {
                            "type": "string",
                            "description": "Type to filter (conversations, decisions, snippets, architecture)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "How many to return",
                            "default": 50
                        }
                    }
                }
            }
        }
    
    def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        """Handle a tool call and return results"""
        try:
            if tool_name == "search_memory":
                return self._search_memory(tool_input)
            elif tool_name == "get_relevant_context":
                return self._get_relevant_context(tool_input)
            elif tool_name == "save_decision":
                return self._save_decision(tool_input)
            elif tool_name == "save_code_snippet":
                return self._save_code_snippet(tool_input)
            elif tool_name == "save_architecture_note":
                return self._save_architecture_note(tool_input)
            elif tool_name == "list_memories":
                return self._list_memories(tool_input)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return {"error": str(e)}
    
    def _search_memory(self, params: dict) -> dict:
        """Search memory"""
        try:
            query = params.get("query")
            memory_type = params.get("memory_type")
            limit = params.get("limit", 10)
            
            if not query:
                return {"error": "query is required"}
            
            weaviate = get_weaviate_service()
            results = weaviate.semantic_search(query, limit, memory_type)
            
            return {
                "query": query,
                "count": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"error": str(e)}
    
    def _get_relevant_context(self, params: dict) -> dict:
        """Get relevant context"""
        try:
            query = params.get("query")
            limit = params.get("limit", 5)
            
            if not query:
                return {"error": "query is required"}
            
            weaviate = get_weaviate_service()
            db = SessionLocal()
            
            # Get semantic results
            search_results = weaviate.semantic_search(query, limit)
            
            # Get recent decisions
            recent_decisions = db.query(DesignDecision)\
                .filter(DesignDecision.status == "active")\
                .order_by(DesignDecision.date_made.desc())\
                .limit(3).all()
            
            db.close()
            
            return {
                "query": query,
                "semantic_results": search_results,
                "recent_decisions": [{
                    "decision": d.decision,
                    "rationale": d.rationale
                } for d in recent_decisions]
            }
        except Exception as e:
            logger.error(f"Get context failed: {e}")
            return {"error": str(e)}
    
    def _save_decision(self, params: dict) -> dict:
        """Save a decision"""
        try:
            decision = params.get("decision")
            rationale = params.get("rationale")
            impact = params.get("impact")
            
            if not decision:
                return {"error": "decision is required"}
            
            db = SessionLocal()
            
            design_decision = DesignDecision(
                decision=decision,
                rationale=rationale,
                impact=impact,
                status="active"
            )
            
            db.add(design_decision)
            db.commit()
            db.refresh(design_decision)
            
            # Try to index in Weaviate
            try:
                weaviate = get_weaviate_service()
                weaviate.index_decision(
                    str(design_decision.id),
                    decision,
                    rationale or decision
                )
            except:
                pass  # Weaviate might not be ready yet
            
            db.close()
            
            return {
                "success": True,
                "id": str(design_decision.id),
                "decision": decision
            }
        except Exception as e:
            logger.error(f"Save decision failed: {e}")
            return {"error": str(e)}
    
    def _save_code_snippet(self, params: dict) -> dict:
        """Save a code snippet"""
        try:
            title = params.get("title")
            code_content = params.get("code_content")
            language = params.get("language")
            description = params.get("description")
            tags = params.get("tags", [])
            
            if not title or not code_content:
                return {"error": "title and code_content are required"}
            
            db = SessionLocal()
            
            snippet = CodeSnippet(
                title=title,
                code_content=code_content,
                language=language,
                description=description,
                tags=tags
            )
            
            db.add(snippet)
            db.commit()
            db.refresh(snippet)
            
            # Try to index in Weaviate
            try:
                weaviate = get_weaviate_service()
                weaviate.index_code_snippet(
                    str(snippet.id),
                    title,
                    code_content,
                    description or title
                )
            except:
                pass
            
            db.close()
            
            return {
                "success": True,
                "id": str(snippet.id),
                "title": title
            }
        except Exception as e:
            logger.error(f"Save snippet failed: {e}")
            return {"error": str(e)}
    
    def _save_architecture_note(self, params: dict) -> dict:
        """Save architecture note"""
        try:
            component = params.get("component")
            description = params.get("description")
            note_type = params.get("note_type", "general")
            tags = params.get("tags", [])
            
            if not component or not description:
                return {"error": "component and description are required"}
            
            db = SessionLocal()
            
            arch_note = ArchitectureNote(
                component=component,
                description=description,
                type=note_type,
                tags=tags,
                status="active"
            )
            
            db.add(arch_note)
            db.commit()
            db.refresh(arch_note)
            
            # Try to index in Weaviate
            try:
                weaviate = get_weaviate_service()
                weaviate.index_architecture_note(
                    str(arch_note.id),
                    component,
                    description
                )
            except:
                pass
            
            db.close()
            
            return {
                "success": True,
                "id": str(arch_note.id),
                "component": component
            }
        except Exception as e:
            logger.error(f"Save architecture note failed: {e}")
            return {"error": str(e)}
    
    def _list_memories(self, params: dict) -> dict:
        """List memories"""
        try:
            memory_type = params.get("memory_type")
            limit = params.get("limit", 50)
            
            db = SessionLocal()
            results = []
            
            if memory_type in ["decisions", None]:
                decisions = db.query(DesignDecision)\
                    .order_by(DesignDecision.date_made.desc())\
                    .limit(limit).all()
                results.extend([{
                    "id": str(d.id),
                    "type": "decision",
                    "decision": d.decision[:100],
                    "status": d.status
                } for d in decisions])
            
            if memory_type in ["snippets", None]:
                snippets = db.query(CodeSnippet)\
                    .order_by(CodeSnippet.created_at.desc())\
                    .limit(limit).all()
                results.extend([{
                    "id": str(s.id),
                    "type": "snippet",
                    "title": s.title,
                    "language": s.language
                } for s in snippets])
            
            db.close()
            
            return {
                "count": len(results),
                "items": results
            }
        except Exception as e:
            logger.error(f"List memories failed: {e}")
            return {"error": str(e)}


def main():
    """Run the MCP server"""
    server = MCPServer()
    
    # Simple stdio-based MCP protocol handler
    logger.info("BrainCell MCP Server starting on stdio")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            message = json.loads(line)
            logger.debug(f"Received: {message}")
            
            # Handle MCP messages
            if message.get("jsonrpc") == "2.0":
                if message.get("method") == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {
                                    "maxDurationMs": 60000
                                }
                            },
                            "serverInfo": {
                                "name": "BrainCell",
                                "version": "1.0.0"
                            }
                        },
                        "id": message.get("id")
                    }
                    print(json.dumps(response))
                
                elif message.get("method") == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "result": {
                            "tools": [
                                {
                                    "name": name,
                                    "description": tool["description"],
                                    "inputSchema": tool["inputSchema"]
                                }
                                for name, tool in server.tools.items()
                            ]
                        },
                        "id": message.get("id")
                    }
                    print(json.dumps(response))
                
                elif message.get("method") == "tools/call":
                    params = message.get("params", {})
                    tool_name = params.get("name")
                    tool_input = params.get("arguments", {})
                    
                    result = server.handle_tool_call(tool_name, tool_input)
                    
                    response = {
                        "jsonrpc": "2.0",
                        "result": {
                            "toolUseId": message.get("id"),
                            "toolResult": result
                        },
                        "id": message.get("id")
                    }
                    print(json.dumps(response))
                
                else:
                    # Unknown method
                    response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": "Method not found"
                        },
                        "id": message.get("id")
                    }
                    print(json.dumps(response))
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
        except Exception as e:
            logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
