# BrainCell — REST API Endpoints

Base URL: `http://localhost:9504`

All list endpoints return a JSON array. All create/update endpoints accept and return JSON objects. Times are ISO 8601 UTC.

---

## Interactions

### `POST /api/interactions`
Store a single agent/user message. Triggers auto-detection of sub-entities (research questions, snippets, files, IOCs, decisions).

```json
{
  "conversation_id": "uuid (optional)",
  "session_id": "uuid (optional)",
  "role": "user | assistant | system",
  "content": "string",
  "message_type": "string (optional)",
  "tokens_used": 150,
  "meta_data": {}
}
```

### `GET /api/interactions`
List all interactions.

### `GET /api/interactions/{id}`

---

## Conversations

### `POST /api/conversations`
```json
{
  "session_name": "string",
  "summary": "string (optional)",
  "meta_data": {}
}
```

### `GET /api/conversations`
### `GET /api/conversations/{id}`
### `PUT /api/conversations/{id}`
### `DELETE /api/conversations/{id}`

---

## Sessions

### `POST /api/sessions`
```json
{
  "session_name": "string",
  "start_time": "datetime (optional)",
  "summary": "string (optional)",
  "meta_data": {}
}
```

### `GET /api/sessions`
### `GET /api/sessions/{id}`
### `PUT /api/sessions/{id}`
```json
{
  "status": "active | completed | archived",
  "summary": "string (optional)",
  "end_time": "datetime (optional)"
}
```
### `DELETE /api/sessions/{id}`

---

## Notes

### `POST /api/notes`
```json
{
  "title": "string",
  "content": "string",
  "tags": ["string"],
  "source": "manual | auto",
  "meta_data": {}
}
```

### `GET /api/notes`
### `GET /api/notes/{id}`
### `PUT /api/notes/{id}`
### `DELETE /api/notes/{id}`

---

## Design Decisions

### `POST /api/decisions`
```json
{
  "decision": "string",
  "rationale": "string",
  "impact": "string",
  "status": "active | superseded | rejected",
  "date_made": "datetime (optional)",
  "meta_data": {}
}
```

### `GET /api/decisions`
### `GET /api/decisions/{id}`
### `PUT /api/decisions/{id}`
### `DELETE /api/decisions/{id}`

---

## Architecture Notes

### `POST /api/architecture-notes`
```json
{
  "component": "string",
  "description": "string",
  "tags": [],
  "meta_data": {}
}
```

### `GET /api/architecture-notes`
### `GET /api/architecture-notes/{id}`
### `PUT /api/architecture-notes/{id}`
### `DELETE /api/architecture-notes/{id}`

---

## Code Snippets

### `POST /api/snippets`
```json
{
  "title": "string",
  "code_content": "string",
  "language": "python | javascript | typescript | go | ...",
  "file_path": "string (optional)",
  "line_start": 1,
  "line_end": 20,
  "description": "string (optional)",
  "tags": [],
  "meta_data": {}
}
```

### `GET /api/snippets?language=python`
### `GET /api/snippets/{id}`
### `PUT /api/snippets/{id}`
### `DELETE /api/snippets/{id}`

---

## Files Discussed

### `POST /api/files`
```json
{
  "file_path": "string",
  "language": "python | ...",
  "description": "string (optional)",
  "tags": [],
  "meta_data": {}
}
```

### `GET /api/files?language=python`
### `GET /api/files/{id}`
### `DELETE /api/files/{id}`

---

## Research Questions

### `POST /api/research-questions`
```json
{
  "question": "string",
  "status": "pending | investigating | answered | closed",
  "priority": "low | medium | high",
  "context": "string (optional)",
  "answer": "string (optional)",
  "source": "auto_detected | manual",
  "tags": [],
  "meta_data": {}
}
```

### `GET /api/research-questions`
Filter: `?status=pending`, `?priority=high`

### `GET /api/research-questions/{id}`
### `PUT /api/research-questions/{id}`
### `DELETE /api/research-questions/{id}`

---

## Tasks

### `POST /api/tasks`
```json
{
  "title": "string",
  "description": "string (optional)",
  "status": "open | in_progress | blocked | done | cancelled",
  "priority": "critical | high | medium | low",
  "assignee": "string (optional)",
  "project": "string (optional)",
  "due_date": "datetime (optional)",
  "tags": [],
  "meta_data": {}
}
```

### `GET /api/tasks`
Filter: `?status_filter=open`, `?priority=high`, `?project=braincell`, `?assignee=alice`

### `GET /api/tasks/open`
Shortcut — returns all `open`, `in_progress`, `blocked` tasks.
Filter: `?project=braincell`

### `GET /api/tasks/{id}`
### `PUT /api/tasks/{id}`
Status change to `done` automatically sets `completed_at`.
### `DELETE /api/tasks/{id}`

---

## Security Incidents

### `POST /api/incidents`
```json
{
  "title": "string",
  "description": "string",
  "severity": "critical | high | medium | low | info",
  "status": "open | investigating | contained | resolved | closed",
  "attack_vector": "phishing | exploit | insider | supply-chain | ...",
  "affected_assets": ["host1", "service2"],
  "mitre_tactics": ["TA0001", "TA0002"],
  "threat_actor_name": "string (optional)",
  "classification_level": "UNCLASSIFIED | CONFIDENTIAL | SECRET",
  "tlp_level": "WHITE | GREEN | AMBER | RED",
  "ioc_refs": ["1.2.3.4", "abc123"],
  "timeline": [{"timestamp": "ISO8601", "event": "string", "analyst": "string"}],
  "meta_data": {}
}
```

### `GET /api/incidents`
Filter: `?severity=critical`, `?status=open`

### `GET /api/incidents/{id}`
### `PUT /api/incidents/{id}`
### `DELETE /api/incidents/{id}`

---

## IOCs (Indicators of Compromise)

### `POST /api/iocs`
Type is auto-detected from value if not provided.

```json
{
  "type": "ip | domain | hash_md5 | hash_sha1 | hash_sha256 | url | email | cve | yara",
  "value": "1.2.3.4",
  "confidence": 0.9,
  "severity": "critical | high | medium | low",
  "status": "active | expired | false_positive | under_review",
  "first_seen": "datetime (optional)",
  "last_seen": "datetime (optional)",
  "expiry_date": "datetime (optional)",
  "source": "OSINT | internal | ISAC | vendor",
  "tags": [],
  "context": "string",
  "incident_refs": ["incident_id"],
  "threat_actor_refs": ["APT28"],
  "classification_level": "UNCLASSIFIED",
  "tlp_level": "GREEN",
  "meta_data": {}
}
```

### `GET /api/iocs`
Filter: `?type=ip`, `?status=active`, `?severity=high`

### `GET /api/iocs/{id}`
### `PUT /api/iocs/{id}`
### `DELETE /api/iocs/{id}`

---

## Threat Actors

### `POST /api/threats`
```json
{
  "name": "string",
  "aliases": ["APT28", "Fancy Bear"],
  "classification": "apt | criminal | hacktivist | state-sponsored | unknown",
  "origin_country": "RU",
  "motivation": "espionage | financial | disruption | ideological",
  "sophistication": "low | medium | high | nation-state",
  "ttps": ["T1566", "T1059.001"],
  "status": "active | inactive | unknown",
  "confidence_score": 0.85,
  "stix_id": "intrusion-set--...",
  "meta_data": {}
}
```

### `GET /api/threats`
### `GET /api/threats/{id}`
### `PUT /api/threats/{id}`
### `DELETE /api/threats/{id}`

---

## Intel Reports

### `POST /api/intel_reports`
```json
{
  "title": "string",
  "summary": "string (optional)",
  "content": "string (Markdown, optional)",
  "classification_level": "UNCLASSIFIED",
  "tlp_level": "WHITE | GREEN | AMBER | RED",
  "source": "OSINT | HUMINT | SIGINT | internal",
  "analyst": "string",
  "confidence_score": 0.8,
  "report_date": "datetime",
  "valid_until": "datetime (optional)",
  "tags": [],
  "ioc_refs": [],
  "threat_actor_refs": [],
  "incident_refs": [],
  "mitre_techniques": ["T1566", "T1059"],
  "meta_data": {}
}
```

### `GET /api/intel_reports`
### `GET /api/intel_reports/{id}`
### `PUT /api/intel_reports/{id}`
### `DELETE /api/intel_reports/{id}`

---

## Vuln Patches

Stores a vulnerable code snippet alongside its patched version for training and reference.

### `POST /api/vuln_patches`
```json
{
  "title": "string",
  "description": "string (optional)",
  "language": "python | javascript | java | go | c | ...",
  "category": "sql_injection | xss | buffer_overflow | path_traversal | ...",
  "severity": "critical | high | medium | low",
  "confidence_score": 1.0,
  "vulnerable_code": "string (required)",
  "patched_code": "string (required)",
  "patch_explanation": "string (optional)",
  "cve_refs": ["CVE-2021-44228"],
  "cwe_refs": ["CWE-89"],
  "owasp_refs": ["A03:2021"],
  "source": "nvd | internal | osv | manual",
  "tags": [],
  "meta_data": {}
}
```

### `GET /api/vuln_patches`
Filter: `?language=python`, `?severity=critical`, `?category=sql_injection`

### `GET /api/vuln_patches/{id}`
### `PUT /api/vuln_patches/{id}`
### `DELETE /api/vuln_patches/{id}`

---

## Runbooks

### `POST /api/runbooks`
```json
{
  "title": "string",
  "description": "string (optional)",
  "category": "incident_response | deployment | maintenance | onboarding | backup | rollback",
  "trigger": "string (optional, when to run this)",
  "prerequisites": "string (optional)",
  "steps": [
    {
      "step": 1,
      "title": "string",
      "command": "string (optional)",
      "expected_output": "string (optional)",
      "notes": "string (optional)"
    }
  ],
  "rollback_steps": [],
  "severity": "P1 | P2 | P3 (optional, incident runbooks only)",
  "services": ["service-a", "service-b"],
  "tags": [],
  "meta_data": {}
}
```

### `GET /api/runbooks`
Filter: `?category=incident_response`, `?severity=P1`

### `GET /api/runbooks/{id}`
### `PUT /api/runbooks/{id}`
### `DELETE /api/runbooks/{id}`

---

## Dependencies

Software package inventory with vulnerability tracking.

### `POST /api/dependencies`
```json
{
  "name": "requests",
  "version": "2.28.1",
  "ecosystem": "pypi | npm | nuget | maven | cargo | go | gem",
  "project": "string (optional)",
  "license": "MIT | Apache-2.0 | GPL-3.0 | ...",
  "status": "ok | vulnerable | deprecated | outdated | unknown",
  "cve_refs": ["CVE-2022-40896"],
  "upgrade_to": "2.31.0 (optional)",
  "notes": "string (optional)",
  "tags": [],
  "meta_data": {}
}
```

### `GET /api/dependencies`
Filter: `?status=vulnerable`, `?ecosystem=pypi`, `?project=braincell`

### `GET /api/dependencies/{id}`
### `PUT /api/dependencies/{id}`
### `DELETE /api/dependencies/{id}`

---

## API Contracts

Track versioned API specifications.

### `POST /api/api_contracts`
```json
{
  "title": "string",
  "service_name": "ITL Control Plane API",
  "version": "v2.1.0",
  "base_url": "https://api.example.com/v2",
  "spec_format": "openapi | graphql | grpc | rest | soap",
  "spec_content": "string (full spec or extract, optional)",
  "status": "active | deprecated | draft | sunset",
  "breaking_changes": "string (optional)",
  "changelog": [{"version": "v2.1.0", "date": "2025-01-01", "summary": "...", "breaking": false}],
  "endpoints": [{"method": "GET", "path": "/health", "summary": "...", "deprecated": false}],
  "auth_type": "bearer | apikey | oauth2 | none",
  "tags": [],
  "meta_data": {}
}
```

### `GET /api/api_contracts`
Filter: `?service_name=...`, `?status=active`

### `GET /api/api_contracts/{id}`
### `PUT /api/api_contracts/{id}`
### `DELETE /api/api_contracts/{id}`

---

## Jobs

Weaviate-only (vector search). No SQL backing table.

### `POST /api/jobs`
```json
{
  "title": "string",
  "description": "string",
  "tags": []
}
```

### `GET /api/jobs/search?q=kubernetes`
Semantic search over job descriptions.

---

## Global Search

### `POST /api/search`
Semantic search across all Weaviate-enabled cells.

```json
{
  "query": "authentication design decision",
  "limit": 10
}
```

### `POST /api/search/conversations`
### `POST /api/search/decisions`
### `POST /api/search/code`
### `POST /api/search/architecture-notes`
### `POST /api/search/files`
### `POST /api/search/sessions`
### `POST /api/search/incidents`
### `POST /api/search/iocs`
### `POST /api/search/threats`

---

## Health

### `GET /health`
```json
{ "status": "ok", "service": "BrainCell" }
```
