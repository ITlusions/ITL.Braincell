"""
BrainCell MCP Client Library

A Python client for interacting with the BrainCell MCP Server.
Simplifies access to persistent memory from any agent or application.

Usage:
    from braincell_mcp_client import BrainCellMCPClient
    
    client = BrainCellMCPClient(base_url="http://localhost:9506")
    
    # Search memory
    results = client.search_memory("authentication patterns")
    
    # Save decision
    client.save_decision(
        decision="Use JWT for API authentication",
        rationale="Stateless, scalable solution"
    )
    
    # Get relevant context
    context = client.get_relevant_context("designing new service")
"""

import requests
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrainCellMCPClient:
    """Client for interacting with BrainCell MCP Server"""
    
    def __init__(self, base_url: str = "http://localhost:9506", timeout: int = 30):
        """
        Initialize the BrainCell MCP Client
        
        Args:
            base_url: Base URL of the MCP server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        
        # Verify connection
        try:
            self.health_check()
            logger.info(f"✓ Connected to BrainCell MCP Server at {base_url}")
        except Exception as e:
            logger.warning(f"⚠ Failed to connect to BrainCell MCP Server: {e}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to MCP server"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {"success": False, "error": str(e)}
    
    # =====================================================================
    # Health & Metadata
    # =====================================================================
    
    def health_check(self) -> Dict[str, Any]:
        """Check server health and connectivity"""
        return self._make_request("GET", "/health")
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        response = self._make_request("GET", "/tools")
        return response.get("tools", [])
    
    # =====================================================================
    # Search & Discovery
    # =====================================================================
    
    def search_memory(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        Search across all memory using semantic search
        
        Args:
            query: Natural language search query
            memory_type: Optional filter (conversations, decisions, snippets, etc.)
            limit: Maximum results to return
            threshold: Minimum relevance threshold (0-1)
        
        Returns:
            Search results with relevant memories
        """
        payload = {
            "query": query,
            "memory_type": memory_type,
            "limit": limit,
            "threshold": threshold
        }
        return self._make_request("POST", "/tools/search_memory", json=payload)
    
    def get_relevant_context(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Get the most relevant context for a query
        
        Args:
            query: The query or task description
            limit: Number of context items to return
        
        Returns:
            Relevant context including semantic search results and recent items
        """
        payload = {"query": query, "limit": limit}
        return self._make_request("POST", "/tools/get_relevant_context", json=payload)
    
    def list_memories(
        self,
        memory_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List stored memories
        
        Args:
            memory_type: Type to filter (conversations, decisions, snippets, etc.)
            limit: Maximum items to return
            offset: Number of items to skip
        
        Returns:
            List of memory items
        """
        params = {
            "memory_type": memory_type,
            "limit": limit,
            "offset": offset
        }
        return self._make_request("GET", "/tools/list_memories", json=params)
    
    def retrieve_memory(self, item_id: str, item_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve a specific memory item by ID
        
        Args:
            item_id: UUID of the memory item
            item_type: Optional type filter
        
        Returns:
            The memory item details
        """
        params = {"item_type": item_type} if item_type else {}
        return self._make_request("GET", f"/tools/retrieve_memory/{item_id}", json=params)
    
    # =====================================================================
    # Conversations
    # =====================================================================
    
    def save_conversation(
        self,
        session_id: str,
        topic: str,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save a conversation to memory
        
        Args:
            session_id: Session identifier (UUID format)
            topic: Conversation topic/title
            summary: Optional conversation summary
            metadata: Additional metadata
        
        Returns:
            Response with saved conversation ID and details
        """
        payload = {
            "session_id": session_id,
            "topic": topic,
            "summary": summary,
            "metadata": metadata or {}
        }
        return self._make_request("POST", "/tools/save_conversation", json=payload)
    
    # =====================================================================
    # Design Decisions
    # =====================================================================
    
    def save_decision(
        self,
        decision: str,
        rationale: Optional[str] = None,
        impact: Optional[str] = None,
        status: str = "active",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save a design decision to memory
        
        Args:
            decision: The decision text
            rationale: Why this decision was made
            impact: Impact of this decision
            status: Decision status (active, archived, superseded)
            metadata: Additional metadata
        
        Returns:
            Response with saved decision ID
        """
        payload = {
            "decision": decision,
            "rationale": rationale,
            "impact": impact,
            "status": status,
            "metadata": metadata or {}
        }
        return self._make_request("POST", "/tools/save_decision", json=payload)
    
    # =====================================================================
    # Architecture Notes
    # =====================================================================
    
    def save_architecture_note(
        self,
        component: str,
        description: str,
        note_type: str = "general",
        status: str = "active",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save architecture notes to memory
        
        Args:
            component: Component name
            description: Detailed description
            note_type: Type of note (general, design, pattern, etc.)
            status: Note status (active, archived)
            tags: List of tags for organization
            metadata: Additional metadata
        
        Returns:
            Response with saved note ID
        """
        payload = {
            "component": component,
            "description": description,
            "note_type": note_type,
            "status": status,
            "tags": tags or [],
            "metadata": metadata or {}
        }
        return self._make_request("POST", "/tools/save_architecture_note", json=payload)
    
    # =====================================================================
    # Code Snippets
    # =====================================================================
    
    def save_code_snippet(
        self,
        title: str,
        code_content: str,
        language: Optional[str] = None,
        file_path: Optional[str] = None,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save code snippets to memory
        
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
        
        Returns:
            Response with saved snippet ID
        """
        payload = {
            "title": title,
            "code_content": code_content,
            "language": language,
            "file_path": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "description": description,
            "tags": tags or [],
            "metadata": metadata or {}
        }
        return self._make_request("POST", "/tools/save_code_snippet", json=payload)
    
    # =====================================================================
    # Context Snapshots
    # =====================================================================
    
    def save_context_snapshot(
        self,
        snapshot_name: str,
        context_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save a complete context snapshot
        
        Args:
            snapshot_name: Name/identifier for the snapshot
            context_data: The full context data as JSON
            metadata: Additional metadata
        
        Returns:
            Response with saved snapshot ID
        """
        payload = {
            "snapshot_name": snapshot_name,
            "context_data": context_data,
            "metadata": metadata or {}
        }
        return self._make_request("POST", "/tools/save_context_snapshot", json=payload)
    
    # =====================================================================
    # Convenience Methods
    # =====================================================================
    
    def search_decisions(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for design decisions"""
        return self.search_memory(query, memory_type="decisions", limit=limit)
    
    def search_code_snippets(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for code snippets"""
        return self.search_memory(query, memory_type="snippets", limit=limit)
    
    def search_architecture(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for architecture notes"""
        return self.search_memory(query, memory_type="architecture", limit=limit)
    
    def search_conversations(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for conversations"""
        return self.search_memory(query, memory_type="conversations", limit=limit)
    
    def get_recent_decisions(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent design decisions"""
        return self.list_memories(memory_type="decisions", limit=limit)
    
    def get_recent_snippets(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent code snippets"""
        return self.list_memories(memory_type="snippets", limit=limit)
    
    def get_recent_architecture_notes(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent architecture notes"""
        return self.list_memories(memory_type="architecture", limit=limit)
    
    def get_recent_conversations(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent conversations"""
        return self.list_memories(memory_type="conversations", limit=limit)
    
    # =====================================================================
    # Utility Methods
    # =====================================================================
    
    def print_memory_summary(self) -> None:
        """Print a summary of stored memories"""
        try:
            conversations = self.get_recent_conversations(limit=3)
            decisions = self.get_recent_decisions(limit=3)
            snippets = self.get_recent_snippets(limit=3)
            architecture = self.get_recent_architecture_notes(limit=3)
            
            print("\n📚 BrainCell Memory Summary")
            print("=" * 50)
            
            if conversations.get('data'):
                print(f"\n💬 Recent Conversations ({conversations['data'].get('count', 0)})")
                for item in conversations['data'].get('items', [])[:3]:
                    print(f"   · {item.get('topic', 'N/A')}")
            
            if decisions.get('data'):
                print(f"\n🎯 Recent Decisions ({decisions['data'].get('count', 0)})")
                for item in decisions['data'].get('items', [])[:3]:
                    print(f"   · {item.get('decision', 'N/A')[:60]}...")
            
            if snippets.get('data'):
                print(f"\n📝 Recent Snippets ({snippets['data'].get('count', 0)})")
                for item in snippets['data'].get('items', [])[:3]:
                    print(f"   · {item.get('title', 'N/A')} ({item.get('language', 'unknown')})")
            
            if architecture.get('data'):
                print(f"\n🏗️ Architecture Notes ({architecture['data'].get('count', 0)})")
                for item in architecture['data'].get('items', [])[:3]:
                    print(f"   · {item.get('component', 'N/A')}")
            
            print("\n" + "=" * 50 + "\n")
        except Exception as e:
            logger.error(f"Failed to print summary: {e}")


# Convenience function for quick access
def create_braincell_client(
    base_url: str = "http://localhost:9506"
) -> BrainCellMCPClient:
    """Create and return a BrainCell MCP client"""
    return BrainCellMCPClient(base_url)


if __name__ == "__main__":
    # Example usage
    print("BrainCell MCP Client Library")
    print("=" * 50)
    
    # Create client
    client = BrainCellMCPClient()
    
    # Check health
    health = client.health_check()
    print(f"\n✓ Server Health: {health.get('status', 'unknown')}")
    
    # List tools
    tools = client.list_tools()
    print(f"\n✓ Available Tools: {len(tools)}")
    for tool in tools[:3]:
        print(f"   · {tool['name']}")
    
    # Print memory summary
    client.print_memory_summary()
    
    print("\n✓ Client ready for use!")
