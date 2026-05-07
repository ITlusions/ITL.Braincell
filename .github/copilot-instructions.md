# ITL.BrainCell — Copilot Instructions

## Project

BrainCell: persistent memory platform (AI agents + devs). PostgreSQL + Weaviate + Redis. Exposed via REST API and MCP.

- **Package**: `itl-braincell` v0.1.0 | **Python** `>=3.12`
- **Key deps**: FastAPI, SQLAlchemy (async), Weaviate v4, Alembic, Pydantic v2, structlog

## Repos (`https://github.com/ITlusions/<name>`)

| Repo | Role |
|---|---|
| ITL.BrainCell | Core library — cells, services, base |
| ITL.BrainCell.Api | REST API (FastAPI) — port 9504 |
| ITL.BrainCell.Mcp | MCP server (FastMCP) — port 9506 |
| ITL.BrainCell.Dashboard | Web UI — port 9507 |

## Source Layout (`src/`)

- `main.py` — FastAPI app, lifespan, CORS, cell route registration
- `cells/__init__.py` — `discover_cells()` auto-scans `cells/<name>/cell.py`
- `cells/base.py` — `MemoryCell` ABC
- `cells/<name>/` — `cell.py`, `model.py`, `schema.py`, `routes.py`
- `api/dependencies.py` — `get_session`, `get_weaviate`
- `mcp/server_http.py` — default MCP (FastMCP, streamable HTTP); `server_stdio.py` — Claude Desktop
- **DO NOT USE** `mcp/server.py` (prototype)

## Cell Architecture

Each cell is a self-contained memory domain. `discover_cells()` registers them at startup — no manual wiring.

**`MemoryCell` contract**: implement `name` (snake_case), `prefix` ("/api/…"), `get_router()`, `get_models()`, `register_mcp_tools(mcp)`.

## Coding Rules

- `cell.py` must export `cell = SomeName()` (MemoryCell instance)
- `async def` for all route handlers
- Weaviate cells: implement `get_weaviate_collection()` for schema setup
- MCP tools: override `register_mcp_tools(mcp)` — no edits to `server_http.py`
- List endpoints → JSON array; times → ISO 8601 UTC; ARM-style nested resources
- Auth: `get_current_identity()` FastAPI dep (Keycloak JWT, Sprint 1)
- Tenant isolation: PostgreSQL schema per tenant (Sprint 2)
- Relative imports within `src/`; never import removed/renamed modules
- Auth roles: `itl-cell-admin`, `itl-cell-writer`, `itl-cell-reader`, `itl-cell-auditor` | Realm: `itl` | Client: `itl-braincell`

## Docs — always update with code

| Change | File |
|---|---|
| New/removed cell | `docs/api/ARCHITECTURE.md` |
| New endpoint | `docs/api/ENDPOINTS.md` |
| New MCP tool | `docs/mcp/GUIDE.md` |
| New env var | `docs/deployment/DOCKER.md` |
| Roadmap done | `docs/roadmap/README.md` |

## Services & Ports

REST API 9504 · MCP 9506 · Dashboard 9507 · PostgreSQL 9500 · Weaviate 9501 · Redis 9503 · pgAdmin 9505

## Git

- Branch: `feature/api-<issue>-<desc>` | Commit: `feat(<scope>): <desc> [Api#<n>]` | PR: `Closes #<n>`
- GitHub projects: #19 Security/Multi-Tenancy · #20 Ingest Pipeline · #26 MCP Cell Tools

## Run Locally

```bash
docker compose up -d
pytest  # or .\run_tests.ps1 -TestType all
```
