# BrainCell MCP Server - Quick Reference

## What is BrainCell MCP Server?

A Model Context Protocol (MCP) server that exposes BrainCell's persistent memory capabilities. Any agent with MCP support can search stored memories, save decisions and code snippets, and retrieve relevant context.

- Search design decisions, code snippets, and architecture notes (SQL ILIKE text search)
- Store new decisions, snippets, and architecture notes
- Retrieve relevant context for a task
- List stored items by type

## Quick Start

```bash
cd ITL.BrainCell
docker-compose up -d braincell-mcp
curl http://localhost:9506/health
```

## Connection

| Endpoint | URL |
|----------|-----|
| MCP Server | `http://localhost:9506` |
| Health Check | `http://localhost:9506/health` |

## Available Tools (6 Total)

### Search and Retrieve
- `search_memory(query, entity_types, limit)` - Text search across decisions, snippets, and notes
- `get_relevant_context(query, limit)` - Text search combined with recent active decisions
- `list_memories(memory_type, limit)` - Browse stored items by type

### Storage
- `save_decision(decision, rationale, impact)` - Record a design decision
- `save_architecture_note(component, description, note_type, tags)` - Document architecture
- `save_code_snippet(title, code_content, language, description, tags)` - Save a code pattern

Note: There is no `save_conversation`, `save_context_snapshot`, or `retrieve_memory` tool. Use the REST API (port 9504) for full conversation and session management.

## API Examples (curl)

```bash
# Health check
curl http://localhost:9506/health

# Search memory
curl -X POST http://localhost:9506/tools/search_memory \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication"}'

# Save decision
curl -X POST http://localhost:9506/tools/save_decision \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "Use Keycloak for SSO",
    "rationale": "Standard in organisation",
    "impact": "Requires additional infrastructure"
  }'

# Get relevant context
curl -X POST http://localhost:9506/tools/get_relevant_context \
  -H "Content-Type: application/json" \
  -d '{"query": "How to handle caching?"}'

# List stored decisions
curl -X POST http://localhost:9506/tools/list_memories \
  -H "Content-Type: application/json" \
  -d '{"memory_type": "decisions", "limit": 20}'
```

## Server Variants

| File | Use Case |
|------|----------|
| `src/mcp/server_http.py` | Production (Docker, Streamable HTTP) |
| `src/mcp/server_stdio.py` | Claude Desktop (stdio transport) |
| `src/mcp/server_lean.py` | Lightweight fallback |
| `src/mcp/server.py` | Legacy, do not use |

## Data Flow

```mermaid
graph LR
    AG["Agent<br/>GitHub Copilot · Claude Desktop"]
    SRV["MCP Server<br/>Port 9506"]
    PG[("PostgreSQL<br/>SQL ILIKE search")]
    API["REST API<br/>Port 9504"]
    WV[("Weaviate<br/>Semantic search")]

    AG -->|"MCP Protocol"| SRV
    SRV -->|"SQL query"| PG
    AG -->|"HTTP"| API
    API -->|"vector search"| WV

    style AG fill:#1565C0,color:#fff
    style SRV fill:#2E7D32,color:#fff
    style PG fill:#37474F,color:#fff
    style API fill:#E65100,color:#fff
    style WV fill:#6A1B9A,color:#fff
```

> The MCP server uses SQL ILIKE (PostgreSQL). Weaviate semantic search is only available through the REST API on port 9504.

## Environment

```bash
DATABASE_URL=postgresql://braincell:password@localhost:5432/braincell
WEAVIATE_URL=http://localhost:8080
REDIS_URL=redis://localhost:6379
ENVIRONMENT=development
```
