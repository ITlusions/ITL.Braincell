# API Endpoints Reference

Complete reference of all REST API endpoints organized by entity type.

---

## Base URL
```
http://localhost:9504/api
```

## Health & Status

### Health Check
```
GET /health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "weaviate_connected": true,
  "environment": "development",
  "uptime_seconds": 3600
}
```

---

## Conversations

### Create Conversation
```
POST /conversations
```

**Request Body**:
```json
{
  "session_id": "uuid-5678",
  "topic": "Project Architecture Discussion",
  "summary": "Discussing modular design approach",
  "metadata": {}
}
```

**Response** (201 Created):
```json
{
  "id": "uuid-1234",
  "topic": "Project Architecture Discussion",
  "summary": "Discussing modular design approach",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "metadata": {}
}
```

### Get Conversation
```
GET /conversations/{conversation_id}
```

**Response** (200 OK):
```json
{
  "id": "uuid-1234",
  "topic": "Project Architecture Discussion",
  "summary": "Discussing modular design approach",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "metadata": {}
}
```

**Error** (404 Not Found):
```json
{
  "detail": "Conversation uuid-1234 not found"
}
```

### Update Conversation
```
PUT /conversations/{conversation_id}
```

**Request Body** (all fields optional):
```json
{
  "topic": "Updated Topic",
  "summary": "Updated summary"
}
```

**Response** (200 OK): Updated conversation object

### Delete Conversation
```
DELETE /conversations/{conversation_id}
```

**Response** (204 No Content): Empty body

**Side Effects**: Deletes all associated interactions, removes from Weaviate

---

## Interactions

### Create Interaction (Message)
```
POST /interactions
```

**Request Body**:
```json
{
  "conversation_id": "uuid-1234",
  "session_id": "uuid-5678",
  "role": "user",
  "message_type": "text",
  "content": "How should we structure the API?",
  "metadata": {}
}
```

**Response** (201 Created):
```json
{
  "id": "uuid-9999",
  "conversation_id": "uuid-1234",
  "session_id": "uuid-5678",
  "role": "user",
  "message_type": "text",
  "content": "How should we structure the API?",
  "created_at": "2024-01-15T10:31:00Z",
  "updated_at": "2024-01-15T10:31:00Z",
  "metadata": {}
}
```

### Get Interaction
```
GET /interactions/{interaction_id}
```

**Response** (200 OK): Interaction object

### Get Conversation Interactions (Nested)
```
GET /interactions/conversations/{conversation_id}/interactions
```

**Response** (200 OK):
```json
[
  {
    "id": "uuid-9999",
    "role": "user",
    "content": "How should we structure the API?",
    "created_at": "2024-01-15T10:31:00Z"
  },
  {
    "id": "uuid-8888",
    "role": "assistant",
    "content": "Consider a modular architecture...",
    "created_at": "2024-01-15T10:32:00Z"
  }
]
```

### Update Interaction
```
PUT /interactions/{interaction_id}
```

**Request Body** (partial):
```json
{
  "content": "Updated message content"
}
```

**Response** (200 OK): Updated interaction

### Delete Interaction
```
DELETE /interactions/{interaction_id}
```

**Response** (204 No Content)

---

## Design Decisions

### Create Decision
```
POST /decisions
```

**Request Body**:
```json
{
  "decision_text": "Use modular API architecture with separate route files",
  "rationale": "Improves maintainability and testability",
  "status": "approved",
  "date_made": "2024-01-15"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid-4567",
  "decision_text": "Use modular API architecture with separate route files",
  "rationale": "Improves maintainability and testability",
  "status": "approved",
  "date_made": "2024-01-15",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Get All Decisions (with optional filter)
```
GET /decisions
GET /decisions?status=approved
```

**Response** (200 OK):
```json
[
  {
    "id": "uuid-4567",
    "decision_text": "Use modular API architecture...",
    "status": "approved"
  },
  {
    "id": "uuid-4568",
    "decision_text": "Implement vector database...",
    "status": "pending"
  }
]
```

### Get Single Decision
```
GET /decisions/{decision_id}
```

**Response** (200 OK): Decision object

### Update Decision
```
PUT /decisions/{decision_id}
```

**Request Body**:
```json
{
  "status": "archived"
}
```

**Response** (200 OK): Updated decision

### Delete Decision
```
DELETE /decisions/{decision_id}
```

**Response** (204 No Content)

---

## Architecture Notes

### Create Architecture Note
```
POST /architecture-notes
```

**Request Body**:
```json
{
  "component": "Authentication",
  "description": "Uses JWT tokens with Keycloak integration",
  "note_type": "general",
  "tags": ["security", "infrastructure"]
}
```

**Response** (201 Created):
```json
{
  "id": "uuid-7890",
  "component": "Authentication",
  "description": "Uses JWT tokens with Keycloak integration",
  "note_type": "general",
  "tags": ["security", "infrastructure"],
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Get All Architecture Notes (with optional filter)
```
GET /architecture-notes
GET /architecture-notes?component=Authentication
```

**Response** (200 OK): Array of notes

### Get Single Note
```
GET /architecture-notes/{note_id}
```

**Response** (200 OK): Note object

### Update Architecture Note
```
PUT /architecture-notes/{note_id}
```

**Request Body** (partial):
```json
{
  "description": "Updated description of architecture"
}
```

**Response** (200 OK): Updated note

### Delete Architecture Note
```
DELETE /architecture-notes/{note_id}
```

**Response** (204 No Content)

---

## Files Discussed

### Create File Discussion
```
POST /files
```

**Request Body**:
```json
{
  "file_path": "src/api/routes/conversations.py",
  "language": "python",
  "purpose": "Conversation route handlers",
  "description": "CRUD endpoints for managing conversations"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid-2345",
  "file_path": "src/api/routes/conversations.py",
  "language": "python",
  "purpose": "Conversation route handlers",
  "description": "CRUD endpoints for managing conversations",
  "discussion_count": 1,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Note**: If file_path already exists, returns existing file with discussion_count incremented

### Get All Files (with optional filter)
```
GET /files
GET /files?language=python
```

**Response** (200 OK): Array of files

### Get Single File
```
GET /files/{file_id}
```

**Response** (200 OK): File object

### Update File
```
PUT /files/{file_id}
```

**Request Body**:
```json
{
  "description": "Updated description"
}
```

**Response** (200 OK): Updated file

### Delete File
```
DELETE /files/{file_id}
```

**Response** (204 No Content)

---

## Code Snippets

### Create Snippet
```
POST /snippets
```

**Request Body**:
```json
{
  "title": "FastAPI Router Pattern",
  "description": "Example of creating a modular router",
  "code_content": "router = APIRouter()\n\n@router.post('')\nasync def create_item(data: ItemCreate):\n    return data",
  "language": "python",
  "tags": ["fastapi", "patterns"]
}
```

**Response** (201 Created):
```json
{
  "id": "uuid-3456",
  "title": "FastAPI Router Pattern",
  "language": "python",
  "discussion_count": 0,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Get All Snippets (with optional filter)
```
GET /snippets
GET /snippets?language=javascript
```

**Response** (200 OK): Array of snippets

### Get Single Snippet
```
GET /snippets/{snippet_id}
```

**Response** (200 OK): Snippet object (includes code_content)

### Update Snippet
```
PUT /snippets/{snippet_id}
```

**Request Body**:
```json
{
  "code_content": "Updated code here"
}
```

**Response** (200 OK): Updated snippet

### Delete Snippet
```
DELETE /snippets/{snippet_id}
```

**Response** (204 No Content)

---

## Memory Sessions

### Create Session
```
POST /sessions
```

**Request Body**:
```json
{
  "session_name": "API Refactoring Session 1",
  "summary": "Discussed modular architecture approach",
  "status": "active",
  "metadata": {
    "focus_area": "API layer",
    "participants": ["dev1", "dev2"]
  }
}
```

**Response** (201 Created):
```json
{
  "id": "uuid-5678",
  "session_name": "API Refactoring Session 1",
  "summary": "Discussed modular architecture approach",
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "metadata": {}
}
```

### Get Session
```
GET /sessions/{session_id}
```

**Response** (200 OK): Session object with all details

### Update Session
```
PUT /sessions/{session_id}
```

**Request Body** (partial update):
```json
{
  "status": "completed",
  "summary": "Completed architecture refactoring discussion"
}
```

**Response** (200 OK): Updated session

### Delete Session
```
DELETE /sessions/{session_id}
```

**Response** (204 No Content)

---

## Semantic Search

All search endpoints use POST with a query object.

### Search Conversations
```
POST /search/conversations
```

**Request Body**:
```json
{
  "query": "modular architecture design",
  "limit": 10,
  "offset": 0
}
```

**Response** (200 OK):
```json
[
  {
    "id": "uuid-1234",
    "type": "conversation",
    "topic": "Project Architecture Discussion",
    "score": 0.87,
    "metadata": {
      "summary": "Discussing modular design approach"
    }
  }
]
```

### Search Interactions
```
POST /search/interactions
```

**Request Body**:
```json
{
  "query": "how to structure API",
  "limit": 10
}
```

**Response**: Array of interaction results with similarity scores

### Search Design Decisions
```
POST /search/decisions
```

**Request Body**:
```json
{
  "query": "architecture decisions",
  "limit": 5
}
```

**Response**: Array of decision results

### Search Architecture Notes
```
POST /search/architecture-notes
```

**Request Body**:
```json
{
  "query": "authentication security",
  "limit": 10
}
```

**Response**: Array of architecture note results

### Search Files
```
POST /search/files
```

**Request Body**:
```json
{
  "query": "route handlers conversation",
  "limit": 10
}
```

**Response**: Array of file results

### Search Code Snippets
```
POST /search/snippets
```

**Request Body**:
```json
{
  "query": "fastapi router pattern",
  "limit": 10
}
```

**Response**: Array of code snippet results

### Search Memory Sessions
```
POST /search/sessions
```

**Request Body**:
```json
{
  "query": "refactoring discussion",
  "limit": 10
}
```

**Response**: Array of session results

---

## Common Response Patterns

### Success Response (200 OK / 201 Created)
```json
{
  "id": "uuid",
  "field1": "value1",
  "field2": "value2",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### List Response (200 OK)
```json
[
  { "id": "1", "field": "value1" },
  { "id": "2", "field": "value2" }
]
```

### Error Response (4xx / 5xx)
```json
{
  "detail": "Descriptive error message"
}
```

---

## Status Codes Summary

| Code | Meaning | Used When |
|------|---------|-----------|
| 200 | OK | GET, PUT successful |
| 201 | Created | POST successful |
| 204 | No Content | DELETE successful |
| 400 | Bad Request | Invalid input format |
| 404 | Not Found | Entity doesn't exist |
| 500 | Server Error | Unexpected error |

---

## Authentication

Currently no authentication. Future: Add JWT token validation via Keycloak.

```
Header: Authorization: Bearer {token}
```

---

## Pagination

Search endpoints support pagination:

```json
{
  "query": "search term",
  "limit": 10,
  "offset": 0
}
```

- `limit`: Number of results (default 10)
- `offset`: Number of results to skip (default 0)

---

## Rate Limiting

Currently unlimited. Future: Implement rate limiting per user/API key.

---

## CORS

CORS enabled for all endpoints. Client must include:
```
Origin: http://localhost:3000
```

---

Example requests using curl:

```bash
# Create conversation
curl -X POST http://localhost:9504/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"topic": "Test", "summary": "Test conversation"}'

# Get conversation
curl http://localhost:9504/api/conversations/uuid-1234

# Search
curl -X POST http://localhost:9504/api/search/conversations \
  -H "Content-Type: application/json" \
  -d '{"query": "architecture", "limit": 5}'

# Health check
curl http://localhost:9504/health
```

---

**Last Updated**: 2024-01-15  
**API Version**: 1.0  
**Documentation Version**: 1.0
