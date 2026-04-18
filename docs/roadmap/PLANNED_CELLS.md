# Planned Cells

New memory cells to be added to BrainCell. Each cell follows the standard structure:
`src/cells/<name>/cell.py`, `model.py`, `schema.py` + `init/<N>_<name>.sql` + Weaviate collection.

---

## `tasks` — Action items & TODOs

**Status**: `planned`

### Why
Action items appear in every session ("ik ga X doen", "todo:", "action item") but are never stored. They disappear after the conversation ends.

### Auto-detection trigger
`role='user'` or `role='assistant'` + one of:
- `todo:`, `to-do:`
- `ik ga .+ doen`, `ik moet .+ regelen`
- `action item`, `actiepunt`
- `\[ \]` checkbox syntax in markdown

### Model fields
| Field | Type | Notes |
|-------|------|-------|
| `title` | str | Short description of the task |
| `description` | str | Full context from the message |
| `status` | enum | `open` / `in_progress` / `done` / `cancelled` |
| `priority` | enum | `low` / `medium` / `high` |
| `due_date` | datetime | Optional |
| `source_interaction_id` | UUID | Interaction that triggered this |
| `source` | enum | `auto_detected` / `manual` |

### MCP tools
- `task_save` — create a task manually
- `task_list` — list by status/priority
- `task_update` — change status/priority/due_date
- `task_search` — semantic search

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
