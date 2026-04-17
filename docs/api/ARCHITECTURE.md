# BrainCell Architecture

## System Overview

Three external entry points share a single data layer. The REST API handles programmatic CRUD and semantic search; the MCP Server exposes tool calls for Copilot and Claude; the Dashboard provides browser-based memory inspection. pgAdmin is an ops-only admin interface.

```mermaid
graph TD
    C(["**Clients**<br/>Copilot · Claude · Users"])

    C -->|"HTTP REST"| API
    C -->|"HTTP browser"| DASH
    C -->|"MCP Protocol"| MCP

    subgraph app["Application Layer"]
        API["**REST API**<br/>Port 9504 · FastAPI<br/>src/main.py"]
        MCP["**MCP Server**<br/>Port 9506 · FastMCP<br/>src/mcp/server_http.py"]
        DASH["**Dashboard**<br/>Port 9507 · Web UI"]
    end

    subgraph data["Data Layer"]
        PG[("**PostgreSQL**<br/>Port 9500<br/>Source of truth")]
        WV[("**Weaviate**<br/>Port 9501 / 9502<br/>Semantic search")]
        RD[("**Redis**<br/>Port 9503<br/>Cache")]
    end

    PGA["**pgAdmin**<br/>Port 9505"]

    API --> PG
    API --> WV
    API --> RD
    MCP --> PG
    MCP --> WV
    DASH --> PG
    PGA -.->|"admin only"| PG
```

---

## Services and Ports

BrainCell runs as multiple independent services:

| Service | Port | Purpose |
|---------|------|---------|
| REST API | 9504 | Programmatic access — CRUD and semantic search |
| Dashboard | 9507 | Browser-based memory explorer |
| MCP Server | 9506 | GitHub Copilot / Claude integration |
| PostgreSQL | 9500 | Structured data (source of truth) |
| Weaviate HTTP | 9501 | Vector search |
| Weaviate gRPC | 9502 | Vector search (gRPC) |
| Redis | 9503 | Caching |
| pgAdmin | 9505 | Database admin UI |

The REST API and Dashboard are separate containers that share PostgreSQL, Weaviate, and Redis.

---

## Directory Structure

```
src/
├── main.py                  # FastAPI application entry point
│
├── api/                     # REST API layer
│   ├── dependencies.py      # Shared dependency injection
│   └── routes/
│       ├── __init__.py      # Route registration (create_routes())
│       ├── health.py        # /health
│       ├── conversations.py # Conversation CRUD + vector sync
│       ├── interactions.py  # Message CRUD + vector sync
│       ├── decisions.py     # Decision CRUD + vector sync
│       ├── architecture_notes.py  # Architecture note CRUD + vector sync
│       ├── files.py         # File tracking CRUD + vector sync
│       ├── snippets.py      # Code snippet CRUD + vector sync
│       ├── sessions.py      # Session CRUD + vector sync
│       ├── jobs.py          # Job tracking
│       ├── admin.py         # /admin/sync, /admin/health
│       └── search.py        # Semantic search (all entity types)
│
├── core/
│   ├── config.py            # Settings class
│   ├── database.py          # DB connection
│   ├── models.py            # SQLAlchemy ORM (8 entity types)
│   └── schemas.py           # Pydantic validation schemas
│
├── mcp/
│   ├── server_http.py       # Production — FastMCP, Streamable HTTP
│   ├── server_lean.py       # Lightweight fallback
│   ├── server_stdio.py      # Local / Claude Desktop
│   └── server.py            # Legacy (do not use)
│
├── services/
│   ├── weaviate_service.py  # Vector DB operations
│   └── sync_service.py      # PostgreSQL → Weaviate startup sync
│
└── web/
    ├── app.py               # Dashboard FastAPI app (port 8001)
    └── router.py            # Jinja2 dashboard routes
```

---

## Module Layers

A strict top-down dependency hierarchy. Each layer only calls the one directly below it — routes never touch the database directly, and the service layer never handles HTTP concerns. Copy this diagram to show the dependency direction in code reviews.

```mermaid
graph TD
    A["**API Layer** — Stateless<br/>routes/ · one file per entity<br/>handles HTTP ↔ Python"]
    B["**Dependencies Layer**<br/>get_db() → SQLAlchemy Session<br/>get_weaviate() → WeaviateService"]
    C["**Service Layer** — Business Logic<br/>weaviate_service.py<br/>index · update · delete · search"]
    D["**Core Layer** — Data Structures<br/>models.py — SQLAlchemy ORM · 8 entity types<br/>schemas.py — Pydantic validation"]
    E["**External Services**<br/>PostgreSQL · Weaviate · Redis"]

    A <-->|"Depends()"| B
    B <--> C
    C <--> D
    D <--> E

    style A fill:#1565C0,color:#fff
    style B fill:#E65100,color:#fff
    style C fill:#2E7D32,color:#fff
    style D fill:#6A1B9A,color:#fff
    style E fill:#37474F,color:#fff
```

---

## Dual-Write Pattern

Every write operation uses this pattern. PostgreSQL is always written first (ACID); Weaviate is synced second and a failure there never fails the request — it only logs a warning.

```mermaid
sequenceDiagram
    participant C as Client
    participant R as FastAPI Route
    participant PG as PostgreSQL
    participant WV as Weaviate

    C->>R: POST /api/conversations
    Note over R: Pydantic validates ConversationCreate<br/>(library call — not a separate service)
    R->>PG: INSERT conversations
    PG-->>R: Committed (ACID — source of truth)
    R->>WV: index_conversation(id, topic, summary)
    Note over WV: Failure logs a warning<br/>but does NOT block the response
    WV-->>R: OK
    R-->>C: 201 ConversationResponse
```

Rules:
- PostgreSQL write failure → return error to client
- Weaviate sync failure → log warning, still return success
- Data is searchable immediately after the PostgreSQL write (Weaviate indexing may lag slightly)

---

## Entity Types

8 entity types stored in PostgreSQL, mirrored in Weaviate:

| Entity | PostgreSQL Table | Weaviate Collection |
|--------|-----------------|---------------------|
| Conversation | conversations | Conversation |
| Interaction | interactions | Interaction |
| DesignDecision | design_decisions | Decision |
| ArchitectureNote | architecture_notes | ArchitectureNote |
| FileDiscussed | files_discussed | FileDiscussed |
| CodeSnippet | code_snippets | CodeSnippet |
| MemorySession | memory_sessions | MemorySession |
| Job | — (Weaviate only) | Job |

Entity relationships:

The three session-scoped entities form a strict parent-child hierarchy. The remaining four entities are **standalone** — they have no foreign keys to other entities and are stored and searched independently.

**Relational hierarchy** (MemorySession → Conversation → Interaction):

```mermaid
erDiagram
    MemorySession ||--o{ Conversation : "has many"
    Conversation ||--o{ Interaction : "has many"

    MemorySession {
        string session_name
        string summary
        string status
    }
    Conversation {
        string topic
        string summary
        uuid session_id
    }
    Interaction {
        string role
        string content
        uuid conversation_id
    }
```

**Standalone entities** (no parent-child relations — directly searchable via vector index):

```mermaid
graph LR
    subgraph standalone["Standalone Entities — Searchable via Weaviate"]
        DD["**DesignDecision**<br/>decision · rationale · status"]
        AN["**ArchitectureNote**<br/>component · description · type"]
        FD["**FileDiscussed**<br/>file_path · description · language"]
        CS["**CodeSnippet**<br/>title · code_content · language"]
    end

    style DD fill:#1565C0,color:#fff
    style AN fill:#2E7D32,color:#fff
    style FD fill:#E65100,color:#fff
    style CS fill:#6A1B9A,color:#fff
```

---

## Request Flow Examples

### Create (POST)

Shows the two-phase write: first PostgreSQL (blocking — failure returns an error), then Weaviate (non-blocking — failure only logs a warning). Both paths converge on a successful 201 response.

```mermaid
flowchart TD
    A(["POST /api/conversations"]) --> B["Pydantic validation<br/>ConversationCreate"]
    B --> C["SQLAlchemy INSERT<br/>PostgreSQL"]
    C --> D{"PG write OK?"}
    D -->|No| E(["Return 4xx / 5xx"])
    D -->|Yes| F["weaviate_service<br/>index_conversation()"]
    F --> G{"Weaviate sync OK?"}
    G -->|No| H["Log warning<br/>(non-blocking)"]
    G -->|Yes| I(["Return 201 ConversationResponse"])
    H --> I

    style E fill:#c0392b,color:#fff
    style I fill:#27ae60,color:#fff
```

### Search (POST /api/search/*)

Text is vectorised by Weaviate's `text2vec-transformers`, then matched against stored embeddings using HNSW approximate nearest-neighbour search. The route converts the raw vector distance into a `similarity_score` (0–1) before returning results.

```mermaid
sequenceDiagram
    participant C as Client
    participant A as FastAPI
    participant WV as Weaviate HNSW

    C->>A: POST /api/search/conversations<br/>{"query": "...", "limit": 10}
    A->>WV: search("Conversation", query, limit)
    WV-->>A: ranked vectors + distances
    A->>A: calculate similarity_score from distance
    A-->>C: [{id, type, score, metadata}, ...]
```

---

## Performance Characteristics

| Operation | Typical Latency | Notes |
|-----------|----------------|-------|
| GET /api/{id} | ~5ms | Direct SQL lookup |
| POST /api | ~50ms | SQL insert + Weaviate sync |
| PUT /api/{id} | ~60ms | SQL update + re-index |
| DELETE /api/{id} | ~40ms | SQL delete + vector removal |
| POST /api/search | ~200ms | Weaviate HNSW vector search |

Weaviate uses HNSW indexing (~O(log n) search performance) with text2vec-transformers for embeddings.

---

## Weaviate Schema

On startup, the system creates these Weaviate collections if they don't exist. Each field listed here is indexed for vector search. Use this diagram to understand the shape of data returned by `GET /api/search/*` endpoints.

```mermaid
classDiagram
    direction LR
    class Conversation {
        +String topic
        +String summary
        +UUID session_id
    }
    class Decision {
        +String decision
        +String rationale
        +String status
    }
    class ArchitectureNote {
        +String component
        +String description
        +String type
        +String tags
    }
    class FileDiscussed {
        +String file_path
        +String description
        +String language
    }
    class CodeSnippet {
        +String title
        +String code_content
        +String language
        +String tags
    }
    class Interaction {
        +String role
        +String content
        +UUID conversation_id
    }
    class MemorySession {
        +String session_name
        +String summary
        +String status
    }
    class Job {
        +String type
        +String status
        +String result
    }
```

All collections use HNSW indexing with the `text2vec-transformers` vectorizer.

---

## API Endpoint Groups

| Group | Prefix | Purpose |
|-------|--------|---------|
| Health | `/health` | Service health check |
| Conversations | `/api/conversations` | Conversation management |
| Interactions | `/api/interactions` | Message and interaction tracking |
| Decisions | `/api/decisions` | Design decision documentation |
| Architecture Notes | `/api/architecture-notes` | Architecture note storage |
| Files | `/api/files` | File discussion tracking |
| Snippets | `/api/snippets` | Code snippet storage |
| Sessions | `/api/sessions` | Memory session management |
| Search — Conversations | `/api/search/conversations` | Semantic search: conversations |
| Search — Decisions | `/api/search/decisions` | Semantic search: design decisions |
| Search — Snippets | `/api/search/snippets` | Semantic search: code snippets |
| Search — Interactions | `/api/search/interactions` | Semantic search: interactions |
| Search — Notes | `/api/search/notes` | Semantic search: architecture notes |
| Search — Files | `/api/search/files` | Semantic search: files |
| Search — General | `/api/search/general` | Semantic search: all entity types |
| Admin | `/admin/sync` | Trigger PostgreSQL → Weaviate full sync |
| Admin | `/admin/health` | Detailed service health with version info |

---

## MCP vs REST API

| Feature                 | MCP Server (9506)         | REST API (9504)               |
|-------------------------|---------------------------|-------------------------------|
| Search method           | SQL ILIKE (PostgreSQL)    | Weaviate vector search        |
| Transport               | Streamable HTTP / stdio   | HTTP REST                     |
| Use case                | Copilot / Claude tools    | Programmatic CRUD access      |
| Entities covered        | decisions, snippets, notes| All 8 entities                |
| Tools / Endpoints       | 6 MCP tools               | 25+ REST endpoints            |
| Authentication          | None (local use)          | None (local use)              |

MCP tools: `search_memory`, `get_relevant_context`, `save_decision`,
`save_code_snippet`, `save_architecture_note`, `list_memories`
