# Planned Cells

New memory cells to be added to BrainCell. Each cell follows the standard structure:
`src/cells/<name>/cell.py`, `model.py`, `schema.py` + `init/<N>_<name>.sql` + Weaviate collection.

---

## `tasks` — Action items & TODOs

**Status**: `done` ✅

Fully implemented. REST API: `GET/POST /api/tasks`, `GET/PUT/DELETE /api/tasks/{id}`, shortcut `GET /api/tasks/open`.

### MCP tools (live)
- `tasks_save(title, description?, status?, priority?, assignee?, project?, tags?)`
- `tasks_search(query, limit=20)`
- `tasks_list(status?, project?, priority?, limit=50)`

---

## `references` — URLs & external sources

**Status**: `planned`

### Why
URLs, docs links, GitHub links, StackOverflow references — all shared during sessions but lost immediately after.

### Auto-detection trigger
`https?://[^\s]+` in any message — extract URL + surrounding sentence as context.

### Model fields
| Field | Type | Notes |
|-------|------|-------|
| `url` | str | Full URL |
| `title` | str | Auto-extracted or manual |
| `context` | str | Sentence surrounding the URL |
| `category` | enum | `documentation` / `github` / `stackoverflow` / `article` / `other` |
| `source_interaction_id` | UUID | |

### MCP tools
- `reference_save`
- `reference_list`
- `reference_search`

---

## `errors` — Bugs & exceptions

**Status**: `planned`

### Why
When debugging, errors and their resolutions are mentioned in conversation but never stored. Next time the same error appears, we start from scratch.

### Auto-detection trigger
`role='user'` + one of:
- `Traceback (most recent call last)`
- `Error:`, `Exception:`, `FATAL:`
- Words: `error`, `exception`, `crash`, `bug`, `fout`, `probleem`

### Model fields
| Field | Type | Notes |
|-------|------|-------|
| `error_type` | str | e.g. `KeyError`, `ConnectionRefused` |
| `message` | str | Full error message |
| `context` | str | What we were doing when it happened |
| `resolution` | str | How it was solved (filled in later) |
| `status` | enum | `open` / `resolved` / `wont_fix` |
| `source_interaction_id` | UUID | |

### MCP tools
- `error_save`
- `error_resolve` — link a resolution to an open error
- `error_search` — find similar past errors by semantic search

---

## `persons` — People & roles

**Status**: `planned`

### Why
Conversations mention people, their roles, and responsibilities. This context is lost between sessions.

### Auto-detection trigger
Named entity patterns: `<Name> is (verantwoordelijk voor|responsible for|leads|manages|owns)`, `contact (for|voor) .+ is <Name>`.

### Model fields
| Field | Type | Notes |
|-------|------|-------|
| `name` | str | Person's name |
| `role` | str | Job title or functional role |
| `responsibilities` | list[str] | What they own |
| `contact_info` | str | Email/Slack/Teams (optional) |
| `team` | str | Which team or department |
| `source_interaction_id` | UUID | |

### MCP tools
- `person_save`
- `person_search`
- `person_list`

---

## `versions` — Version tracking

**Status**: `planned`

### Why
Version numbers are mentioned during upgrades, compatibility discussions, and changelogs — but never retained. Knowing "we were on v1.4 when we made this decision" is valuable context.

### Auto-detection trigger
`v\d+\.\d+` or `versie \d+` or `upgrade (naar|to) .+` in any message.

### Model fields
| Field | Type | Notes |
|-------|------|-------|
| `component` | str | Which service/library |
| `version` | str | e.g. `1.4.2` |
| `notes` | str | What changed or why relevant |
| `source_interaction_id` | UUID | |

### MCP tools
- `version_save`
- `version_list` — list all versions per component
