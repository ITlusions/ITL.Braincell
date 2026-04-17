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

| Table               | Description                                      |
|---------------------|--------------------------------------------------|
| `conversations`     | Chat sessions with topic, summary, session_id    |
| `design_decisions`  | Architectural decisions with rationale and impact|
| `architecture_notes`| System component notes with component tags       |
| `files_discussed`   | File references with metadata                    |
| `code_snippets`     | Reusable code examples with language tags        |
| `context_snapshots` | Point-in-time context captures                   |
| `memory_sessions`   | Session grouping and metadata                    |
| `alembic_version`   | Schema migration tracking                        |

---

## Weaviate Schema

Three classes are managed in Weaviate for vector search:

| Class           | Fields                                      |
|-----------------|---------------------------------------------|
| `Conversation`  | topic, summary, session_id, embedding_id    |
| `Decision`      | decision, rationale, embedding_id           |
| `CodeSnippet`   | title, code_content, language, embedding_id |

Weaviate uses `text2vec-transformers` to generate embeddings automatically on insert.

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
  ✓ Connected to PostgreSQL
    - conversations: 5 rows
    - design_decisions: 6 rows
    - architecture_notes: 6 rows
    - files_discussed: 6 rows
    - code_snippets: 5 rows
  ✅ Database contains 28 total records

  ✓ Connected to Weaviate
    - Conversation: ✓ has data
    - Decision: ✓ has data
    - CodeSnippet: ✓ has data
  ✅ Weaviate is configured and ready
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
