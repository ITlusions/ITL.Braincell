# BrainCell MCP Server Guide

## Overview

The BrainCell MCP (Model Context Protocol) server exposes BrainCell's persistent memory capabilities through a standardized protocol. Any agent or application with MCP support can use it to search stored memories, save decisions and code snippets, and retrieve relevant context.

The production server is implemented in `src/mcp/server_http.py` using FastMCP with Streamable HTTP transport.

## Architecture

The MCP server is a thin adapter over the same PostgreSQL database used by the REST API. It does not use Weaviate — searches run as SQL `ILIKE` text queries.

```mermaid
graph TD
    AG["Agent with MCP Support<br/>GitHub Copilot · Claude Desktop"]
    SRV["BrainCell MCP Server<br/>Port 9506 · FastMCP<br/>src/mcp/server_http.py"]
    PG[("PostgreSQL<br/>Port 9500<br/>design_decisions · code_snippets<br/>architecture_notes")]

    AG -->|"MCP Protocol (HTTP)"| SRV
    SRV -->|"SQL ILIKE search"| PG
    PG -->|"Results"| SRV
    SRV -->|"Tool response"| AG

    style AG fill:#1565C0,color:#fff
    style SRV fill:#2E7D32,color:#fff
    style PG fill:#37474F,color:#fff
```

> MCP search uses SQL ILIKE text matching against PostgreSQL. It does not use Weaviate vector search. Weaviate is used by the REST API for semantic search.

## Quick Start

### Start the MCP server

```bash
cd ITL.BrainCell
docker-compose up -d braincell-mcp

# Verify it is running
curl http://localhost:9506/health
```

### Connect to MCP from Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "braincell": {
      "command": "python",
      "args": ["-m", "src.mcp.server_stdio"],
      "cwd": "/path/to/ITL.BrainCell"
    }
  }
}
```

Or connect to the running HTTP server directly (requires an MCP client that supports Streamable HTTP).

## Available Tools

The MCP server exposes 6 tools.

### search_memory

Search across stored design decisions, code snippets, and architecture notes using text matching.

```
Parameters:
  query         string    required  Text to search for
  entity_types  list      optional  Filter by type: "decisions", "snippets", "notes"
  limit         integer   optional  Max results (default: 10)
```

### get_relevant_context

Get the most relevant context for a query. Combines text search with recent active decisions.

```
Parameters:
  query   string    required  Text to search for
  limit   integer   optional  Max results (default: 5)
```

### save_decision

Store a design decision.

```
Parameters:
  decision   string   required  The decision text
  rationale  string   optional  Why this decision was made
  impact     string   optional  Expected impact or consequences
```

### save_code_snippet

Store a reusable code snippet.

```
Parameters:
  title         string         required  Short descriptive title
  code_content  string         required  The code
  language      string         optional  Programming language
  description   string         optional  What the code does
  tags          list[string]   optional  Tags for categorization
```

### save_architecture_note

Store an architecture note about a component.

```
Parameters:
  component    string         required  Component or system name
  description  string         required  What was noted
  note_type    string         optional  Category (e.g., "pattern", "constraint")
  tags         list[string]   optional  Tags for categorization
```

### list_memories

List stored memories of a specific type.

```
Parameters:
  memory_type  string    optional  "decisions", "snippets", or "notes"
  limit        integer   optional  Max results (default: 50)
```

## Server Variants

| File | Use Case |
|------|----------|
| `src/mcp/server_http.py` | Production -- Docker deployment, Streamable HTTP transport |
| `src/mcp/server_stdio.py` | Local use -- Claude Desktop, stdio transport |
| `src/mcp/server_lean.py` | Lightweight fallback -- no FastMCP dependency |
| `src/mcp/server.py` | Legacy -- broken imports, do not use |

## Docker Endpoints

| Service | External Port | Notes |
|---------|---------------|-------|
| BrainCell MCP Server | 9506 | This server |
| BrainCell REST API | 9504 | Full CRUD + Weaviate semantic search |
| PostgreSQL | 9500 | MCP server reads/writes here |
| Weaviate HTTP | 9501 | Used by REST API, not MCP |
| Redis | 9503 | |
| pgAdmin | 9505 | |
| Dashboard | 9507 | |

## Environment Variables

The MCP server reads the same environment as the main API:

```bash
DATABASE_URL=postgresql://user:password@host:5432/braincell
WEAVIATE_URL=http://localhost:8080
REDIS_URL=redis://localhost:6379
ENVIRONMENT=development
```

## Troubleshooting

### Server does not start

```bash
# Check logs
docker-compose logs braincell-mcp

# Common causes:
# - PostgreSQL not ready: wait for healthy status
# - Missing ENV: check docker-compose.yml environment section
```

### Search returns no results

The MCP server uses SQL ILIKE, so results depend on exact word matches. Use broader search terms or check if the relevant items were saved through the REST API or MCP tools.

```bash
# List what is stored
curl http://localhost:9506/tools/list_memories
```

### Connection refused

```bash
# Check container is running
docker-compose ps

# Confirm port mapping
docker-compose port braincell-mcp 9506
```

## Performance Notes

- Search latency is determined by PostgreSQL query performance, not embedding generation.
- Weaviate (semantic search) is only used by the REST API endpoints under `/api/search/`.
- For semantic search over all 8 entity types, use the REST API on port 9504.
