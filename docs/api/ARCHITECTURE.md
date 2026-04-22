# BrainCell — Architecture

## Overview

BrainCell is a persistent memory system for AI agents and developers. It stores structured knowledge across multiple specialised memory cells, combining PostgreSQL (structured data) and Weaviate (semantic vector search).

```
Clients (Copilot · Claude · Users)
        │                   │                   │
     HTTP REST          MCP Protocol        HTTP Browser
        │                   │                   │
   ┌────▼────┐         ┌────▼────┐        ┌────▼────┐
   │ REST API │         │MCP Server│        │Dashboard│
   │Port 9504 │         │Port 9506 │        │Port 9507│
   └────┬────┘         └────┬────┘        └────┬────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
               ┌────────────┼────────────┐
               │            │            │
          ┌────▼───┐  ┌─────▼───┐  ┌────▼──┐
          │Postgres │  │Weaviate │  │ Redis │
          │Port 9500│  │Port 9501│  │Port   │
          │         │  │         │  │9503   │
          └─────────┘  └─────────┘  └───────┘
```

---

## Services & Ports

| Service     | Port | Description                                 |
|-------------|------|---------------------------------------------|
| REST API    | 9504 | FastAPI — all cell CRUD and search routes   |
| MCP Server  | 9506 | FastMCP — memory tools via MCP protocol     |
| Dashboard   | 9507 | Web UI for browsing and managing memory     |
| PostgreSQL  | 9500 | Source of truth for all structured records  |
| Weaviate    | 9501 | Vector DB for semantic search               |
| pgAdmin     | 9505 | Database admin UI (dev only)                |
| Redis       | 9503 | Session cache                               |

---

## Cell Architecture

BrainCell organises memory into self-contained **cells**. Each cell is:

- A directory under `src/cells/<name>/`
- Auto-discovered at startup via `src/cells/__init__.py`
- Responsible for its own PostgreSQL table(s), routes, and MCP tools

### Cell contract (`MemoryCell`)

Every cell exports a `cell` object (instance of `MemoryCell`) from `cell.py`:

```python
class MemoryCell(ABC):
    @property
    def name(self) -> str: ...         # snake_case identifier
    @property
    def prefix(self) -> str: ...       # API route prefix
    def get_router(self) -> APIRouter: ...
    def get_models(self) -> list: ...  # SQLAlchemy model classes
    def register_mcp_tools(self, mcp): ...  # optional MCP tools
```

### Registered cells

| Cell               | Prefix               | Storage        | Description                                  |
|--------------------|----------------------|----------------|----------------------------------------------|
| `interactions`     | `/api/interactions`  | PostgreSQL     | Every agent/user message; auto-detects sub-entities |
| `conversations`    | `/api/conversations` | PostgreSQL     | Named conversation threads                   |
| `sessions`         | `/api/sessions`      | PostgreSQL     | Memory sessions grouping conversations       |
| `decisions`        | `/api/decisions`     | PG + Weaviate  | Design decisions with rationale and impact   |
| `architecture_notes` | `/api/architecture-notes` | PG + Weaviate | Component architecture documentation |
| `snippets`         | `/api/snippets`      | PG + Weaviate  | Reusable code examples                       |
| `files_discussed`  | `/api/files`         | PG + Weaviate  | File paths and descriptions mentioned        |
| `notes`            | `/api/notes`         | PostgreSQL     | Free-form notes with tags                    |
| `research_questions` | `/api/research-questions` | PostgreSQL | Questions auto-detected from interactions |
| `tasks`            | `/api/tasks`         | PostgreSQL     | Action items and backlog tracking            |
| `incidents`        | `/api/incidents`     | PG + Weaviate  | Security incidents (SIRP-style)              |
| `iocs`             | `/api/iocs`          | PG + Weaviate  | Indicators of Compromise (IP, hash, domain, CVE) |
| `threats`          | `/api/threats`       | PG + Weaviate  | Threat actors and TTP profiles               |
| `intel_reports`    | `/api/intel_reports` | PG + Weaviate  | Threat intelligence reports (TLP-marked)     |
| `vuln_patches`     | `/api/vuln_patches`  | PG + Weaviate  | Vulnerable code + patched counterparts       |
| `runbooks`         | `/api/runbooks`      | PostgreSQL     | Operational runbooks and procedures          |
| `dependencies`     | `/api/dependencies`  | PostgreSQL     | Software package inventory                   |
| `api_contracts`    | `/api/api_contracts` | PostgreSQL     | API specifications and changelogs            |
| `jobs`             | `/api/jobs`          | Weaviate only  | Job postings (vector-only, no SQL table)     |

---

## Data Flow

### Write path (REST API)
1. Client sends `POST /api/<cell>/`
2. FastAPI validates via Pydantic schema
3. Cell route writes to PostgreSQL (source of truth)
4. `sync_service` dual-writes searchable fields to Weaviate

### Read / search path
- Exact / filtered: `GET /api/<cell>/?field=value` → PostgreSQL query
- Semantic: `POST /api/search/` or MCP `search_memory` → Weaviate → PostgreSQL hydration

### Auto-detection (on `interactions_save`)
When an interaction is saved via MCP `interactions_save`, the following detectors run automatically:

| Detector           | Trigger                                   | Target cell        |
|--------------------|-------------------------------------------|--------------------|
| Research questions | `role='user'` + question heuristic        | `research_questions` |
| Code snippets      | `role='assistant'` + fenced code block    | `snippets`         |
| Files discussed    | Any role + file path pattern              | `files_discussed`  |
| Design decisions   | `role='assistant'` + decision pattern     | `decisions`        |
| IOCs               | Any role + IP / hash / CVE / domain regex | `iocs`             |
| Auto-answer        | Weaviate distance < 0.25 on pending question | `research_questions` (answered) |

---

## Storage Backends

### PostgreSQL (port 9500)
- Source of truth for all cells
- Indexed on common filter fields (status, priority, project, etc.)
- Managed via Alembic migrations

### Weaviate (port 9501)
- Vector index using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- Cells that support semantic search register their collection at startup
- Soft-delete: archived records are kept in Weaviate but excluded from live results

### Redis (port 9503)
- Session-level cache for frequently accessed context
- Not a source of truth — safe to flush

---

## MCP Server Variants

BrainCell ships four MCP server implementations. See [../mcp/GUIDE.md](../mcp/GUIDE.md) for details.

| File              | Transport    | Use case                            |
|-------------------|--------------|-------------------------------------|
| `server_http.py`  | Streamable HTTP (FastMCP) | Production, remote agents |
| `server_stdio.py` | stdio (JSON-RPC)          | Claude Desktop, local tools |
| `server_lean.py`  | HTTP (legacy FastAPI)     | Minimal, legacy clients   |
| `server.py`       | HTTP (legacy FastAPI)     | Original prototype        |

---

## Environment Variables

| Variable       | Default                                           | Purpose                |
|----------------|---------------------------------------------------|------------------------|
| `DATABASE_URL` | `postgresql://braincell:...@postgres:5432/braincell` | PostgreSQL connection |
| `WEAVIATE_URL` | `http://weaviate:80`                              | Weaviate endpoint      |
| `REDIS_URL`    | `redis://redis:6379`                              | Redis endpoint         |
| `ENVIRONMENT`  | `development`                                     | `development` / `production` |

---

## Adding a New Cell

1. Create `src/cells/<name>/cell.py` — export a `MemoryCell` subclass as `cell`
2. Optionally add `model.py`, `schema.py`, `routes.py`
3. No registration needed — auto-discovered at startup

See `src/cells/base.py` and `src/cells/tasks/` for reference.
