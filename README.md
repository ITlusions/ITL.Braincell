# BrainCell - Centralized Memory for Copilot

A centralized memory system for Copilot that combines PostgreSQL, Weaviate vector database, and JSON storage for semantic search and context management.

## Architecture

```
┌─────────────────────────────────────────┐
│     BrainCell FastAPI Application       │
├─────────────────────────────────────────┤
│ • Conversations & Sessions              │
│ • Design Decisions                      │
│ • Architecture Notes                    │
│ • Code Snippets                         │
│ • Context Snapshots                     │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┬──────────┐
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐
│PG SQL  │ │Weaviate│ │ Redis  │ │P...  │
│        │ │Vector  │ │ Cache  │ │Admin │
│Structs │ │Semantic│ │        │ │      │
└────────┘ └────────┘ └────────┘ └──────┘
```

## Tech Stack

- **Backend**: FastAPI + Python 3.11
- **Database**: PostgreSQL 15 (structured data + JSONB)
- **Vector DB**: Weaviate (semantic search)
- **Cache**: Redis (session caching)
- **Container**: Docker Compose

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Or Python 3.11+ with PostgreSQL and Weaviate

### Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# Access API
curl http://localhost:9504/health

# View Weaviate console
open http://localhost:9501
```

### Access Points

- **API**: `http://localhost:9504`
- **API Docs**: `http://localhost:9504/docs`
- **Weaviate Console**: `http://localhost:9501`
- **PostgreSQL**: `localhost:9500` (user: `braincell`, password: `braincell_dev_password`)
- **Redis**: `localhost:9503`
- **PgAdmin**: `http://localhost:9505` (admin@braincell.local / admin)

### Environment Variables

Create `.env` file:

```bash
DATABASE_URL=postgresql://braincell:braincell_dev_password@localhost:9500/braincell
WEAVIATE_URL=http://localhost:9501
REDIS_URL=redis://localhost:9503
ENVIRONMENT=development
```

## API Endpoints

### Health & Status
- `GET /health` - Health check

### Conversations
- `POST /api/conversations` - Create conversation
- `GET /api/conversations/{id}` - Get conversation
- `PUT /api/conversations/{id}` - Update conversation

### Design Decisions
- `POST /api/decisions` - Create decision
- `GET /api/decisions` - List decisions
- `GET /api/decisions/{id}` - Get decision

### Architecture Notes
- `POST /api/architecture-notes` - Create note
- `GET /api/architecture-notes` - List notes

### Files Discussed
- `POST /api/files` - Record file discussion
- `GET /api/files` - List files

### Code Snippets
- `POST /api/snippets` - Create snippet
- `GET /api/snippets` - List snippets

### Context Snapshots
- `POST /api/snapshots` - Create snapshot
- `GET /api/snapshots` - Get recent snapshots

### Memory Sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions/{id}` - Get session
- `PUT /api/sessions/{id}` - Update session

### Search
- `POST /api/search/conversations` - Semantic search conversations
- `POST /api/search/decisions` - Semantic search decisions
- `POST /api/search/code` - Semantic search code snippets

## Example Usage

### Create a Conversation

```bash
curl -X POST http://localhost:9504/api/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "topic": "Building memory system",
    "summary": "Discussed BrainCell architecture with PostgreSQL and Weaviate",
    "metadata": {"tags": ["architecture", "design"]}
  }'
```

### Create a Design Decision

```bash
curl -X POST http://localhost:9504/api/decisions \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "Use Weaviate for semantic search",
    "rationale": "Better than Redis for vector similarity",
    "impact": "Enables advanced search capabilities",
    "status": "active"
  }'
```

### Search Conversations

```bash
curl -X POST http://localhost:9504/api/search/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "query": "memory system architecture",
    "limit": 10,
    "offset": 0
  }'
```

### Create Code Snippet

```bash
curl -X POST http://localhost:9504/api/snippets \
  -H "Content-Type: application/json" \
  -d '{
    "title": "FastAPI Health Check",
    "code_content": "@app.get(\"/health\")\nasync def health_check():\n    return {\"status\": \"ok\"}",
    "language": "python",
    "file_path": "src/main.py",
    "tags": ["fastapi", "health-check"]
  }'
```

## Database Schema

### Tables

1. **conversations** - Conversation records with timestamps
2. **design_decisions** - Design decisions with rationale and impact
3. **architecture_notes** - Architecture patterns and constraints
4. **files_discussed** - Files mentioned in conversations
5. **code_snippets** - Code examples and snippets
6. **context_snapshots** - Full context snapshots (JSONB)
7. **memory_sessions** - Session tracking and metadata

### Features

- Full-text search on PostgreSQL
- JSONB support for flexible metadata
- Automatic timestamps with triggers
- Vector indexing in Weaviate for semantic search
- Cascading updates with triggers

## Development

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Locally (without Docker)

```bash
# Start PostgreSQL, Weaviate, Redis separately
# Then:
uvicorn src.main:app --reload
```

### Run Tests

```bash
pytest tests/
```

### Format Code

```bash
black src/
ruff check src/
```

## Monitoring

### Logs

```bash
# View application logs
docker-compose logs braincell-api

# Follow logs
docker-compose logs -f braincell-api
```

### Database Queries

Access PostgreSQL directly:

```bash
docker-compose exec postgres psql -U braincell -d braincell
```

### Weaviate Status

```bash
curl http://localhost:8080/v1/.well-known/ready
```

## Cleanup

```bash
# Stop all services
docker-compose down

# Remove volumes (careful!)
docker-compose down -v

# Rebuild everything
docker-compose down -v && docker-compose build --no-cache
```

## Features

- **Structured Data** - PostgreSQL for conversations, decisions, notes
- **Vector Search** - Weaviate for semantic similarity search
- **JSON Storage** - JSONB in PostgreSQL for flexible data
- **Sessions** - Track conversation sessions and context
- **Caching** - Redis for performance
- **Full-Text Search** - PostgreSQL built-in FTS
- **API Docs** - Auto-generated Swagger UI
- **Docker Ready** - Complete docker-compose setup

## Integration with Copilot

The BrainCell API can be integrated with Copilot via:

1. **Direct API calls** from Copilot extensions
2. **Memory context injection** before conversations
3. **Auto-indexing** of sessions and decisions
4. **Semantic search** for context retrieval

## Future Enhancements

- [ ] Graph database for relationship mapping
- [ ] LLM-based summarization
- [ ] Advanced filtering and aggregations
- [ ] Memory export/import
- [ ] Analytics dashboard
- [ ] Multi-tenant support
- [ ] Audit logging
- [ ] Backup and recovery

## Documentation

All technical documentation is in the [`docs/`](./docs/) directory.

### Quick Links

- [Documentation Index](./docs/README.md)
- [Quick Start Guide](./docs/guides/QUICK_START.md)
- [Kubernetes Deployment](./docs/deployment/KUBERNETES.md)
- [MCP Server Guide](./docs/mcp/GUIDE.md)
- [API Endpoints Reference](./docs/api/ENDPOINTS.md)
- [Database Guide](./docs/guides/DATABASE.md)

### Documentation Categories

| Category | Description | Link |
|----------|-------------|------|
| **API & Architecture** | Endpoints, architecture diagrams, service structure | [docs/api/](./docs/api/) |
| **Deployment** | Docker, Kubernetes, Helm charts | [docs/deployment/](./docs/deployment/) |
| **Guides** | Quick starts, database setup | [docs/guides/](./docs/guides/) |
| **MCP Protocol** | Model Context Protocol integration | [docs/mcp/](./docs/mcp/) |
| **Testing** | Test procedures and framework | [docs/testing/](./docs/testing/) |

## License

MIT

## Support

For issues or questions, check the [documentation](./docs/) or open an issue.
