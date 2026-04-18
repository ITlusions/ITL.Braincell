# Intelligence & Cross-Cell Features

Planned improvements that make BrainCell smarter — not just storing more, but connecting and acting on what it knows.

---

## 1. Duplicate detection

**Status**: `planned`
**Priority**: high

### Problem
The same decision or research question can be auto-detected multiple times across separate sessions, creating noise.

### Solution
Before saving a new `decisions` or `research_questions` record, query Weaviate first. If a result with `distance < 0.15` exists → skip insert, optionally increment a `mention_count` field instead.

### Where to implement
`src/cells/interactions/cell.py` — at the start of each detector block:

```python
_existing = _gwvs().search_decisions(query=_sentence, limit=1)
if _existing and _existing[0].get("distance", 1.0) < 0.15:
    pass  # duplicate — skip
else:
    # proceed with save
```

---

## 2. Priority auto-scoring

**Status**: `planned`
**Priority**: medium

### Problem
All auto-detected research questions default to `priority='medium'`. Urgent issues go unnoticed.

### Solution
Detect urgency keywords before saving:

```python
_HIGH_PRIORITY = re.compile(
    r"\b(urgent|critical|kritiek|production|prod|down|blocker|asap|zo snel mogelijk)\b",
    re.IGNORECASE,
)
_priority = "high" if _HIGH_PRIORITY.search(content) else "medium"
```

Apply to: `research_questions`, `tasks`, `errors`.

---

## 3. Session context injection

**Status**: `planned`
**Priority**: high

### Problem
Every session starts blank. BrainCell has rich context but it is never surfaced at the start.

### Solution
When `sessions_save(action="start")` is called, automatically query:
1. Open research questions (status=`pending`, priority=`high`)
2. Last 5 design decisions
3. Most recently discussed files (last 7 days)
4. Open tasks (status=`open`)

Return this as a structured `context_block` in the session response. The calling agent injects it as system context.

### MCP tool change
`sessions_save` response gains a `context_block` field when `action="start"`.

---

## 4. Cross-cell linking

**Status**: `planned`
**Priority**: medium

### Decision ↔ Research question
When a decision is auto-detected and there is a recent pending research question with Weaviate distance < 0.30 → set `source_question_id` on the decision and update the question status to `answered`.

### Snippet ↔ File
When a code snippet contains a recognizable file path → automatically also call `files_discussed` upsert for that path, and set `file_path` on the `CodeSnippet` record.

### Task ↔ Decision
When a task is auto-detected directly after a decision → link `source_decision_id` on the task.

---

## 5. Session auto-summary

**Status**: `planned`
**Priority**: medium

### Problem
At the end of a work session, all context of what was done is inside individual cell records but never aggregated.

### Solution
When `sessions_save(action="end")` is called, auto-generate a summary:

```
Session: 2026-04-18 14:00 → 17:30
  Interactions : 47
  New decisions: 3
  Open questions: 2 (1 answered)
  Files discussed: src/cells/interactions/cell.py, src/services/weaviate_service.py
  New snippets: 4 (Python)
  New tasks: 1 (open)
```

Store as `notes` record with `category='session_summary'`.

---

## 6. Weekly digest tool

**Status**: `planned`
**Priority**: low

### New MCP tool: `memory_digest`

```
memory_digest(period="week")
```

Returns:
- Total interactions in the period
- All new decisions (grouped by status)
- Open research questions
- Most frequently discussed files (top 5)
- New snippets per language
- Open tasks

Useful for weekly team reviews or personal reflection.

---

## 7. Add `ResearchQuestion` to `CELL_MAP`

**Status**: `planned` — **immediate fix needed**
**Priority**: high

### Problem
`src/cells/jobs/cell.py` iterates `CELL_MAP` to archive expired records. `ResearchQuestion` was added later and is missing from the map.

### Fix
```python
# src/cells/jobs/cell.py
from src.cells.research_questions.model import ResearchQuestion

CELL_MAP = [
    ...existing...,
    ("ResearchQuestion", ResearchQuestion),
]
```
