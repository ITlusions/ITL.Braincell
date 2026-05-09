# ITL.BrainCell — Copilot Instructions

## Project

`itl-braincell` is the **core library** for the BrainCell persistent memory platform. It defines all memory cells, data models, services, and database infrastructure. Consumed by ITL.BrainCell.Api, ITL.BrainCell.Mcp, and ITL.BrainCell.Dashboard.

- **Package**: `itl-braincell` v0.1.0 | **Python** `>=3.12`
- **Key deps**: FastAPI, SQLAlchemy (async), Weaviate v4, Alembic, Pydantic v2, structlog

## Repos (`https://github.com/ITlusions/<name>`)

| Repo | Role |
|---|---|
| ITL.BrainCell | **Core library** — cells, services, models, DB infra |
| ITL.BrainCell.Api | REST API (FastAPI) — port 9504 |
| ITL.BrainCell.Mcp | MCP server (FastMCP) — port 9506 |
| ITL.BrainCell.Dashboard | Web UI — port 9507 |

## Source Layout (`src/`)

- `cells/__init__.py` — `discover_cells()` auto-scans `cells/<name>/cell.py`
- `cells/base.py` — `MemoryCell` ABC
- `cells/<name>/` — `cell.py`, `model.py`, `schema.py`, `routes.py`
- `core/config.py` — settings (Pydantic BaseSettings, env-driven)
- `core/database.py` — async SQLAlchemy engine + session factory
- `core/models.py` — shared ORM base
- `core/schemas.py` — shared Pydantic schemas
- `services/` — cross-cell business logic

## Cell Architecture

Each cell is a self-contained memory domain. `discover_cells()` registers them at startup — no manual wiring.

**`MemoryCell` contract**: implement `name` (snake_case), `prefix` ("/api/…"), `get_router()`, `get_models()`, `register_mcp_tools(mcp)`.

## Coding Rules

- `cell.py` must export `cell = SomeName()` (MemoryCell instance)
- `async def` for all route handlers
- Weaviate cells: implement `get_weaviate_collection()` for schema setup
- MCP tools: override `register_mcp_tools(mcp)` — no edits to server files in consuming repos
- List endpoints → JSON array; times → ISO 8601 UTC; ARM-style nested resources
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

## CI/CD Pipeline

Two workflow files in `.github/workflows/`:

| File | Trigger | Purpose |
|---|---|---|
| `ci.yml` | push / PR / dispatch | detect-version → lint+test+build wheel → auto-tag → GitHub Release |
| `publish.yml` | `release: published` | download CI wheel → PyPI (stable) or TestPyPI (pre-release) |

**Branch strategy:**

| Branch | CI | Auto-tag | Publish |
|---|---|---|---|
| `feature/**`, `hotfix/**`, `develop` | lint + test + build | — | — |
| `release/**` | lint + test + build | `vX.Y.Z-rc.N` | TestPyPI |
| `main` | lint + test + build | `vX.Y.Z` | PyPI |

- Wheel is built **once** in `ci.yml` (artifact: `braincell-wheel`). `publish.yml` downloads it — never rebuilds.
- PyPI auth: OIDC Trusted Publisher — no API tokens, no secrets.

## Git

- Branch: `feature/<issue>-<desc>` | `release/vX.Y` | `hotfix/<desc>`
- Commit: `feat(<scope>): <desc>` | `fix(<scope>): <desc>`
- PR: `Closes #<n>` | GitHub projects: #19 Security/Multi-Tenancy · #20 Ingest Pipeline · #26 MCP Cell Tools

## Run Locally

```bash
docker compose up -d
pytest  # or .\run_tests.ps1 -TestType all
```
