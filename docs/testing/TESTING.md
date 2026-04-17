# Testing

This document covers running the BrainCell test suite, test categories, and manual
API / MCP endpoint verification.

---

## Prerequisites

```bash
pip install pytest pytest-asyncio pytest-timeout httpx

# Services must be running
docker compose up -d
```

---

## Running Tests

### All Tests

```bash
pytest
```

### By Category

```bash
pytest -m functional     # Functional correctness
pytest -m edge           # Edge and boundary cases
pytest -m state          # Memory state handling
pytest -m performance    # Response time and load
pytest -m integration    # Cross-tool data integrity
pytest -m critical       # Critical path only
```

### Scripts (CI / Windows)

Linux / macOS:
```bash
chmod +x run_tests.sh
./run_tests.sh all
./run_tests.sh functional
./run_tests.sh performance
./run_tests.sh coverage
```

Windows:
```powershell
.\run_tests.ps1 -TestType all
.\run_tests.ps1 -TestType functional
.\run_tests.ps1 -TestType performance
.\run_tests.ps1 -TestType coverage
```

---

## Test Categories

### 1. Functional (4 tests)

Core behaviour of `get_relevant_context`:

| Test | Description                         |
|------|-------------------------------------|
| 1.1  | Valid query with default limit      |
| 1.2  | Valid query with custom limit       |
| 1.3  | Empty query handling                |
| 1.4  | Semantic relevance validation       |

### 2. Edge Cases (5 tests)

| Test | Description                         |
|------|-------------------------------------|
| 2.1  | Limit = 0                           |
| 2.2  | Limit = 1 (minimum)                 |
| 2.3  | Limit > max (very high value)       |
| 2.4  | Query with special characters       |
| 2.5  | Query with non-ASCII characters     |

### 3. Memory State (4 tests)

| Test | Description                         |
|------|-------------------------------------|
| 3.1  | Empty memory repository             |
| 3.2  | Recent decision retrieval           |
| 3.3  | Relevance ranking correctness       |
| 3.4  | Duplicate filtering                 |

### 4. Performance (3 tests)

| Test | Description                         |
|------|-------------------------------------|
| 4.1  | Response time < 1 second            |
| 4.2  | Large limit handling (100+)         |
| 4.3  | Complex query performance           |

### 5. Integration (3 tests)

| Test | Description                                        |
|------|----------------------------------------------------|
| 5.1  | Results compatible with `save_decision`            |
| 5.2  | Results consistent with `list_memories`            |
| 5.3  | Cross-tool data integrity                          |

---

## Manual API Testing

### Health Check

```bash
curl http://localhost:9504/health
```

### Memories CRUD

```bash
# List all memories
curl http://localhost:9504/api/memories

# Create a memory
curl -X POST http://localhost:9504/api/memories \
  -H "Content-Type: application/json" \
  -d '{"memory_type": "decision", "content": "Use PostgreSQL for structured data", "tags": ["database", "architecture"]}'

# Search memories
curl -X POST http://localhost:9504/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "database optimization", "limit": 5}'
```

### Conversations

```bash
curl http://localhost:9504/api/conversations
curl http://localhost:9504/api/conversations/{id}
```

### Decisions

```bash
curl http://localhost:9504/api/decisions
```

### Code Snippets

```bash
curl http://localhost:9504/api/code-snippets
```

---

## MCP Tool Testing

Test via the `/mcp` endpoint (HTTP POST):

```bash
# search_memory
curl -X POST http://localhost:9506/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_memory",
      "arguments": {"query": "database"}
    }
  }'

# save_decision
curl -X POST http://localhost:9506/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "save_decision",
      "arguments": {
        "decision": "Use Redis for caching",
        "rationale": "Low latency key-value access",
        "impact": "medium"
      }
    }
  }'

# list available tools
curl -X POST http://localhost:9506/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 3, "method": "tools/list"}'
```

---

## Pytest Configuration

`pytest.ini` in the repo root:

```ini
[pytest]
markers =
    functional: Functional test cases
    edge: Edge case test cases
    state: Memory state test cases
    performance: Performance and load tests
    integration: Integration test cases
    slow: Tests that take > 1 second
    critical: Critical path tests (should always pass)

addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings

asyncio_mode = auto
timeout = 30
```

---

## Performance Expectations

| Endpoint               | Expected p95 |
|------------------------|--------------|
| `GET /health`          | < 50 ms      |
| `GET /api/memories`    | < 200 ms     |
| `POST /api/search`     | < 500 ms     |
| MCP tool call          | < 1 s        |

---

## Coverage Report

```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html
```
