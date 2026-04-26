# ITL.BrainCell — Copilot Instructions

## Project

BrainCell is a persistent memory platform for AI agents and developers. It stores structured knowledge across specialised memory **cells**, combining PostgreSQL (structured data) and Weaviate (semantic vector search). Exposed via REST API and MCP (Model Context Protocol).

- **Package**: `itl-braincell` v0.1.0
- **Python**: `>=3.12`
- **Key deps**: FastAPI, SQLAlchemy (async), Weaviate v4, Redis, Alembic, Pydantic v2, structlog

---

## Repository Map

```
ITL.BrainCell          ← core library (cells, services, base)          d:\repos\ITL.BrainCell
ITL.BrainCell.Api      ← REST API service (FastAPI)                    d:\repos\ITL.BrainCell.Api
ITL.BrainCell.Mcp      ← MCP server (FastMCP)                          d:\repos\ITL.BrainCell.Mcp
ITL.BrainCell.Dashboard← Web UI                                        d:\repos\ITL.BrainCell.Dashboard
```

All repos: `https://github.com/ITlusions/<repo-name>`

---

## Source Layout

```
src/
├── main.py             # FastAPI app — lifespan, CORS, cell route registration
├── cells/
│   ├── __init__.py     # discover_cells() — auto-scans cells/<name>/cell.py
│   ├── base.py         # MemoryCell ABC — all cells implement this
│   └── <name>/
│       ├── cell.py     # exports cell = MyCell()  ← required
│       ├── model.py    # SQLAlchemy model
│       ├── schema.py   # Pydantic schema
│       └── routes.py   # FastAPI router
├── core/               # shared utilities
├── services/
│   ├── weaviate_service.py
│   └── sync_service.py
├── api/
│   └── dependencies.py # FastAPI deps (get_session, get_weaviate)
└── mcp/
    ├── server_http.py  # default MCP server (FastMCP, streamable HTTP)
    ├── server_stdio.py # stdio variant (Claude Desktop)
    ├── server_lean.py  # legacy HTTP fallback
    └── server.py       # original prototype — DO NOT USE in new code
```

---

## Cell Architecture

Each **cell** is a self-contained memory domain. No manual registration — `discover_cells()` scans at startup.

### MemoryCell contract

```python
class MemoryCell(ABC):
    @property
    def name(self) -> str: ...          # snake_case
    @property
    def prefix(self) -> str: ...        # "/api/my-cell"
    def get_router(self) -> APIRouter: ...
    def get_models(self) -> list: ...   # SQLAlchemy classes
    def register_mcp_tools(self, mcp): ...  # override to expose MCP tools
```

### Existing cells (under `src/cells/`)

`interactions`, `conversations`, `sessions`, `decisions`, `architecture_notes`, `snippets`, `files_discussed`, `notes`, `research_questions`, `tasks`, `errors`, `persons`, `versions`, `references`, `iocs`, `threats`, `incidents`, `intel_reports`, `vuln_patches`, `runbooks`, `dependencies`, `api_contracts`, `kill_chains`, `vuln_reports`

---

## Coding Rules

### Cell conventions
- `cell.py` must export `cell = SomeName()` (instance of `MemoryCell`)
- Use `async def` for all route handlers
- Weaviate cells: `get_weaviate_collection()` in the cell class for schema setup
- MCP tools: override `register_mcp_tools(mcp)` — no changes to `server_http.py` needed

### API conventions
- All list endpoints return JSON array
- Times in ISO 8601 UTC
- ARM-style nested resources where relevant
- Auth via Keycloak JWT — `get_current_identity()` FastAPI dependency (Sprint 1)
- Tenant isolation via PostgreSQL schema per tenant (Sprint 2)

### Import style
- Use **relative imports** within `src/`
- Never import from removed/renamed modules

### Authentication (Sprint 1 target state)
- `src/auth/keycloak.py` — `HTTPBearer`, JWKS fetch, token validation
- `src/auth/permissions.py` — `require_role()` decorators
- Roles: `itl-cell-admin`, `itl-cell-writer`, `itl-cell-reader`, `itl-cell-auditor`
- Realm: `itl`, Client: `itl-braincell`

---

## Documentation Rules

**Always update `docs/` in the same change as code.**

| Change | File to update |
|--------|----------------|
| New/removed/renamed cell | `docs/api/ARCHITECTURE.md` cells table |
| New endpoint | `docs/api/ENDPOINTS.md` |
| New MCP tool | `docs/mcp/GUIDE.md` |
| New service or port | `docs/api/ARCHITECTURE.md` services table |
| New env variable | `docs/deployment/DOCKER.md` |
| New test category | `docs/testing/TESTING.md` |
| Roadmap item completed | `docs/roadmap/README.md` status column |

---

## Services & Ports

| Service    | Port |
|------------|------|
| REST API   | 9504 |
| MCP Server | 9506 |
| Dashboard  | 9507 |
| PostgreSQL | 9500 |
| Weaviate   | 9501 |
| Redis      | 9503 |
| pgAdmin    | 9505 |

---

## GitHub Project Structure

| Org project | Name                      | Sprint scope             |
|-------------|---------------------------|--------------------------|
| #19         | Security & Multi-Tenancy  | Api Sprint 1 + Sprint 2  |
| #20         | Ingest Pipeline           | Api Sprint 3 + Sprint 5  |
| #26         | MCP Cell Tools            | Mcp Sprint 4 + Sprint 5  |

Sprint → Milestone → [EPIC] issue → sub-issues

```bash
gh issue list --repo ITLusions/ITL.BrainCell.Api --state open
gh project item-list 19 --owner ITLusions
```

---

## Running Locally

```bash
docker compose up -d
curl http://localhost:9504/health

# Tests
pytest
.\run_tests.ps1 -TestType all      # Windows
./run_tests.sh all                  # Linux/macOS
```

---

## Git Workflow

- Branch: `feature/api-<issue-number>-<description>`  
- Commit: `feat(<scope>): <description> [Api#<n>]`  
- PR: `Closes #<n>` — assign to milestone
