# BrainCell API Quick Start

## Starting the System

### Option 1: Docker Compose (Recommended)
```bash
docker-compose up -d
# Wait 10-15 seconds for services to initialize
curl http://localhost:9504/health
```

### Option 2: Local Development
```bash
./setup.ps1          # Windows
./setup.sh          # macOS/Linux

# Start each service separately:
# PostgreSQL, Weaviate, Redis (ensure they're running)

python -m uvicorn src.main:app --reload
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Conversations
```bash
# Create
POST /api/conversations
{
  "session_id": "uuid",
  "topic": "string",
  "summary": "string (optional)",
  "metadata": {}
}

# Get
GET /api/conversations/{id}

# Update
PUT /api/conversations/{id}
{
  "topic": "string (optional)",
  "summary": "string (optional)",
  "metadata": {}
}
```

### Design Decisions
```bash
# Create
POST /api/decisions
{
  "decision": "string",
  "rationale": "string (optional)",
  "impact": "string (optional)",
  "status": "active|archived|superseded"
}

# List (filter by status)
GET /api/decisions?status_filter=active

# Get
GET /api/decisions/{id}
```

### Architecture Notes
```bash
# Create
POST /api/architecture-notes
{
  "component": "string",
  "description": "string",
  "type": "general|pattern|integration|constraint",
  "status": "active|archived|draft",
  "tags": ["string"],
  "metadata": {}
}

# List
GET /api/architecture-notes?component=search_string
```

### Files Discussed
```bash
# Create/Update
POST /api/files
{
  "file_path": "string",
  "description": "string (optional)",
  "language": "python|javascript|etc (optional)",
  "purpose": "string (optional)",
  "metadata": {}
}

# List
GET /api/files?language=python
```

### Code Snippets
```bash
# Create
POST /api/snippets
{
  "title": "string",
  "code_content": "string",
  "language": "string (optional)",
  "file_path": "string (optional)",
  "line_start": 1,
  "line_end": 10,
  "description": "string (optional)",
  "tags": ["string"],
  "metadata": {}
}

# List
GET /api/snippets?language=python
```

### Sessions
```bash
# Create session
POST /api/sessions
{
  "session_name": "string",
  "summary": "string (optional)",
  "metadata": {}
}

# Get session
GET /api/sessions/{id}

# Update session
PUT /api/sessions/{id}
{
  "status": "active|completed|archived",
  "summary": "string (optional)",
  "metadata": {}
}
```

### Semantic Search

The `/api/search/` endpoints use Weaviate vector search.

```bash
# Search conversations
POST /api/search/conversations
{
  "query": "memory system architecture",
  "limit": 10
}

# Search decisions
POST /api/search/decisions
{
  "query": "vector database",
  "limit": 10
}

# Search code snippets
POST /api/search/code
{
  "query": "FastAPI health check",
  "limit": 10
}

# Search architecture notes
POST /api/search/architecture-notes
{
  "query": "caching strategy",
  "limit": 10
}

# Search files
POST /api/search/files
{
  "query": "authentication",
  "limit": 10
}

# Search sessions
POST /api/search/sessions
{
  "query": "implementation session",
  "limit": 10
}
```

## Storage

| Content | Storage | Notes |
|---------|---------|-------|
| Conversations | PostgreSQL | Structured history |
| Decisions | PostgreSQL + Weaviate | Structured + semantic search |
| Architecture Notes | PostgreSQL + Weaviate | Design documentation |
| Code Snippets | PostgreSQL + Weaviate | Reusable code patterns |
| Files | PostgreSQL + Weaviate | File tracking |
| Sessions | PostgreSQL + Weaviate | Session tracking |

## Example Workflows

### Workflow 1: Start a Coding Session
```bash
# 1. Create session
SESSION=$(curl -s -X POST http://localhost:9504/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "session_name": "BrainCell Implementation",
    "summary": "Building vector memory system"
  }' | jq -r '.id')

# 2. Log conversation
curl -X POST http://localhost:9504/api/conversations \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION\",
    \"topic\": \"Architecture discussion\",
    \"summary\": \"Decided on Weaviate for semantic search\"
  }"

# 3. Save files discussed
curl -X POST http://localhost:9504/api/files \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/main.py",
    "language": "python",
    "purpose": "Main FastAPI application"
  }'

# 4. Record decision
curl -X POST http://localhost:9504/api/decisions \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "Use PostgreSQL + Weaviate architecture",
    "rationale": "Best combination of structured and semantic search",
    "impact": "Enables intelligent memory retrieval"
  }'
```

### Workflow 2: Find Related Work
```bash
# Search for similar discussions
curl -X POST http://localhost:9504/api/search/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "query": "vector database implementation",
    "limit": 5
  }'

# Search for relevant code
curl -X POST http://localhost:9504/api/search/code \
  -H "Content-Type: application/json" \
  -d '{
    "query": "database initialization",
    "limit": 5
  }'
```

### Workflow 3: Mark Session Complete
```bash
curl -X PUT http://localhost:9504/api/sessions/{session_id} \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "summary": "Completed core API implementation"
  }'
```

## Access Points

```
API Documentation:  http://localhost:9504/docs
RedDoc:             http://localhost:9504/redoc
PostgreSQL:         localhost:9500
Weaviate Console:   http://localhost:9501
Redis:              localhost:9503
pgAdmin:            http://localhost:9505
Dashboard:          http://localhost:9507
```

## Configuration

Edit `.env` for customization:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
WEAVIATE_URL=http://weaviate:8080
REDIS_URL=redis://redis:6379
ENVIRONMENT=development|production
```

## Common Queries

### Get All Active Decisions
```bash
curl http://localhost:9504/api/decisions?status_filter=active
```

### Get Python Files Discussed
```bash
curl http://localhost:9504/api/files?language=python
```

### Find Related Code
```bash
curl -X POST http://localhost:9504/api/search/code \
  -H "Content-Type: application/json" \
  -d '{
    "query": "src/main.py FastAPI",
    "limit": 10
  }'
```

## Troubleshooting

### Weaviate Connection Failed
- Check: `curl http://localhost:9501/v1/.well-known/ready`
- Restart: `docker-compose restart weaviate`

### Database Connection Issues
- Check: `docker-compose logs postgres`
- Verify: `docker-compose exec postgres psql -U braincell -d braincell -c "\dt"`

### API Not Responding
- Check health: `curl http://localhost:9504/health`
- View logs: `docker-compose logs braincell-api`
- Restart API: `docker-compose restart braincell-api`

## Performance Tips

1. Always set a `limit` parameter (max 100)
2. Use `offset` for pagination on large result sets
3. Filter decisions by status using `status_filter`
4. Redis is configured for caching

## Security Notes

- Disable CORS in production
- Set proper authentication headers
- Use environment variables for secrets
- Enable SSL/TLS for PostgreSQL connections
- Implement rate limiting

See main README.md for complete documentation.

### Option 1: Docker Compose (Recommended)
```bash
docker-compose up -d
# Wait 10-15 seconds for services to initialize
curl http://localhost:9504/health
```

### Option 2: Local Development
```bash
./setup.ps1          # Windows
./setup.sh          # macOS/Linux

# Start each service separately:
# PostgreSQL, Weaviate, Redis (ensure they're running)

python -m uvicorn src.main:app --reload
```

---

## New Cells Quick Reference

The following cells were added beyond the original 5. See [docs/api/ENDPOINTS.md](../api/ENDPOINTS.md) for full request/response bodies.

| Cell | Endpoint prefix | Example |
|------|----------------|---------|
| interactions | `/api/interactions` | `POST /api/interactions` — save a message |
| tasks | `/api/tasks` | `GET /api/tasks/open` — open backlog |
| notes | `/api/notes` | `POST /api/notes` — free-form notes |
| research_questions | `/api/research-questions` | `GET /api/research-questions?status_filter=pending` |
| incidents | `/api/incidents` | `POST /api/incidents` — security incident |
| iocs | `/api/iocs` | `GET /api/iocs?type_filter=ip` |
| threats | `/api/threats` | `POST /api/threats` — threat actor |
| intel_reports | `/api/intel-reports` | `POST /api/intel-reports` |
| vuln_patches | `/api/vuln-patches` | `POST /api/vuln-patches` |
| runbooks | `/api/runbooks` | `GET /api/runbooks/{id}` — full steps |
| dependencies | `/api/dependencies` | `GET /api/dependencies?status_filter=vulnerable` |
| api_contracts | `/api/api-contracts` | `GET /api/api-contracts/services` |

For MCP tools covering all 19 cells, see [docs/mcp/QUICK_REFERENCE.md](../mcp/QUICK_REFERENCE.md).