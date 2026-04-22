# Database — Schema and Operations

This document covers the PostgreSQL schema, Weaviate vector schema, seed data,
and common database operations for local development.

---

## Schema Overview

BrainCell uses two storage backends in tandem:

| Backend    | Port  | Purpose                                      |
|------------|-------|----------------------------------------------|
| PostgreSQL | 9500  | Structured storage, source of truth          |
| Weaviate   | 9501  | Vector index for semantic search             |

Every record written to PostgreSQL is also indexed in Weaviate (dual-write pattern).

---

## PostgreSQL Tables

All 19 cells have their own table. Every table has `id` (UUID PK), `created_at`, and `updated_at`.

| Table                      | Cell               | Description                                              |
|----------------------------|--------------------|----------------------------------------------------------|
| `conversations`            | conversations      | Chat history with topic, summary, session_id             |
| `memory_sessions`          | sessions           | Session grouping with status and summary                 |
| `interactions`             | interactions       | Individual messages (role, content, tokens_used)         |
| `design_decisions`         | decisions          | Architectural decisions with rationale and impact        |
| `architecture_notes`       | architecture_notes | Component-level architecture notes                       |
| `code_snippets`            | snippets           | Reusable code examples with language tags                |
| `files_discussed`          | files_discussed    | File references with path and language                   |
| `cell_notes`               | notes              | Free-form notes with tags and source                     |
| `cell_research_questions`  | research_questions | Questions with status (pending/investigating/answered)   |
| `tasks`                    | tasks              | Action items with status, priority, project, assignee    |
| `security_incidents`       | incidents          | Security incidents with severity, MITRE tactics, IOC refs|
| `iocs`                     | iocs               | Indicators of Compromise with type, confidence, TLP      |
| `threat_actors`            | threats            | APT groups / criminal orgs with TTPs and STIX ID         |
| `intel_reports`            | intel_reports      | Intelligence reports with TLP, confidence, analyst       |
| `vuln_patches`             | vuln_patches       | Vulnerable/patched code pairs with CVE/CWE refs          |
| `runbooks`                 | runbooks           | Step-by-step operational procedures                      |
| `dependencies`             | dependencies       | Package dependencies with version, ecosystem, CVE refs   |
| `api_contracts`            | api_contracts      | API specs (OpenAPI/GraphQL/gRPC) with changelog          |
| `alembic_version`          | —                  | Schema migration tracking                                |

---

## Weaviate Schema

BrainCell creates Weaviate collections for cells that support semantic search. Each collection stores a text representation of the record plus a `source_id` back-reference to PostgreSQL.

| Collection             | Cell               | Primary search fields                          |
|------------------------|--------------------|------------------------------------------------|
| `Conversation`         | conversations      | topic, summary                                 |
| `Decision`             | decisions          | decision, rationale                            |
| `CodeSnippet`          | snippets           | title, description, code_content              |
| `ArchitectureNote`     | architecture_notes | component, description                         |
| `FileDiscussed`        | files_discussed    | file_path, description                         |
| `Note`                 | notes              | title, content                                 |
| `ResearchQuestion`     | research_questions | question, context, answer                      |
| `Task`                 | tasks              | title, description, project                    |
| `SecurityIncident`     | incidents          | title, description, attack_vector              |
| `IOC`                  | iocs               | value, context, source                         |
| `ThreatActor`          | threats            | name, ttps, motivation                         |
| `IntelReport`          | intel_reports      | title, summary, content                        |
| `VulnPatch`            | vuln_patches       | title, vulnerable_code, patch_explanation      |
| `Runbook`              | runbooks           | title, description, trigger                    |
| `Dependency`           | dependencies       | name, notes, cve_refs                          |
| `ApiContract`          | api_contracts      | title, service_name, spec_content             |

The `jobs` cell uses Weaviate as its **only** backend (no PostgreSQL table).

Weaviate uses the `sentence-transformers/all-MiniLM-L6-v2` model (384 dimensions) for embeddings, configured via the `text2vec-transformers` module.

---

## Seed Data (Development)

The `populate_database.py` script inserts realistic sample data into both databases.

### What it creates

| Table               | Sample records |
|---------------------|----------------|
| conversations       | 5              |
| design_decisions    | 6              |
| architecture_notes  | 6              |
| files_discussed     | 6              |
| code_snippets       | 5              |

Sample topics include: microservices architecture, database optimization, security,
CI/CD, and frontend patterns.

### Run the seeder

```bash
# Start services first
docker compose up -d

# Populate both databases
python populate_database.py
```

Windows:

```powershell
.\populate-database.ps1
```

Linux / macOS:

```bash
chmod +x populate-database.sh
./populate-database.sh
```

### Verify the results

```bash
python verify_database.py
```

Expected output:

```
  [OK] Connected to PostgreSQL
    - conversations: 5 rows
    - design_decisions: 6 rows
    - architecture_notes: 6 rows
    - files_discussed: 6 rows
    - code_snippets: 5 rows
  [OK] Database contains 28 total records

  [OK] Connected to Weaviate
    - Conversation: has data
    - Decision: has data
    - CodeSnippet: has data
  [OK] Weaviate is configured and ready
```

---

## Schema Migrations

BrainCell uses Alembic for PostgreSQL migrations.

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe change"

# Check current revision
alembic current

# View migration history
alembic history
```

---

## Common Operations

### Connect via psql

```bash
# Direct connection (Docker)
docker exec -it braincell-postgres psql -U braincell -d braincell

# Via mapped port
psql -h localhost -p 9500 -U braincell -d braincell
```

### Connect via pgAdmin

Open http://localhost:9505

| Field    | Value                   |
|----------|-------------------------|
| Host     | `postgres`              |
| Port     | `5432`                  |
| Database | `braincell`             |
| Username | `braincell`             |
| Password | `braincell_dev_password`|

### Reset the Database

```bash
# Drop all tables and recreate schema
python -c "
from src.database import drop_db, init_db
drop_db()
init_db()
print('Database reset complete')
"

# Re-seed with sample data
python populate_database.py
```

### Manual Backup

```bash
docker exec braincell-postgres \
  pg_dump -U braincell braincell > braincell-backup-$(date +%Y%m%d).sql
```

### Restore from Backup

```bash
docker exec -i braincell-postgres \
  psql -U braincell -d braincell < braincell-backup-20260417.sql
```

---

## Weaviate Operations

### Check Weaviate Status

```bash
curl http://localhost:9501/v1/.well-known/ready
curl http://localhost:9501/v1/schema
```

### Trigger Full Re-sync

If the Weaviate index is out of sync with PostgreSQL:

```bash
curl -X POST http://localhost:9504/admin/sync
```

### Monitor Weaviate

```bash
docker compose logs weaviate -f
```

---

## Troubleshooting

### Connection refused

```bash
# Verify all services are running
docker compose ps
docker compose logs postgres
```

### Weaviate schema missing

Run the population script again — it creates the schema automatically:

```bash
python populate_database.py
```

Or check `src/weaviate_service.py` for the `_ensure_schema()` method.

### Slow first-run embedding

On first insert, `text2vec-transformers` downloads the model and generates embeddings.
This can take ~60 seconds. Subsequent operations are fast (HNSW indexing).

### Data not appearing in search

Verify data exists in Weaviate:

```bash
curl http://localhost:9501/v1/objects?class=Conversation
```

If empty, trigger a re-sync:

```bash
curl -X POST http://localhost:9504/admin/sync
```
