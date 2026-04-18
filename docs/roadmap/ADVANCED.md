# Advanced Features

Advanced capabilities for BrainCell — beyond storing and searching, towards a memory that reasons, connects, and acts proactively.

---

## Layer 1 — Memory that thinks for itself

### Contradiction detection

**Status**: `planned`
**Priority**: high
**Complexity**: medium

When a new `decisions` record is saved, semantically compare it against existing decisions via Weaviate. If `distance < 0.30` but the content is contradictory → flag both as `conflicting` and raise a warning.

This prevents silently overturning a previous architectural decision.

```python
# In decisions detector (interactions/cell.py):
_similar = _gwvs().search_decisions(query=_sentence, limit=3)
for _hit in _similar:
    if _hit.get("distance", 1.0) < 0.30:
        # Flag both as conflicting, raise MCP notification
```

**New fields on `DesignDecision`:**
```python
conflict_ids: Optional[list[str]]  # UUIDs of conflicting decisions
conflict_flag: bool = False
```

---

### Memory consolidation (nightly job)

**Status**: `planned`
**Priority**: medium
**Complexity**: medium

A scheduler (via the `jobs` cell) that runs nightly to:
1. Cluster related `interactions` from the past day using Weaviate
2. Merge them into a higher-order `architecture_note` or `decision`
3. Mark source interactions as `consolidated=true`

Like human memory: loose recollections condense into patterns. Less noise, more signal.

---

### Confidence scoring

**Status**: `planned`
**Priority**: medium
**Complexity**: low

Each time a pattern is reconfirmed → `confidence_score` increases. Useful as a filter: "show only decisions with `confidence > 0.7`."

**New fields on all cells (via mixin):**
```python
confidence_score: float = 0.5  # 0.0 - 1.0
mention_count: int = 1         # incremented on each reconfirmation
```

---

## Layer 2 — Temporal reasoning

### Time-travel queries

**Status**: `planned`
**Priority**: low
**Complexity**: low

"What did the architecture look like 3 months ago?" — all records have `created_at`. By adding an `as_of` parameter to search tools, you can reconstruct the state of memory at any point in time.

**API addition:**
```
GET /api/v1/decisions/search?q=authentication&as_of=2026-01-01
```

Valuable for post-mortems and audits.

---

### Drift detection

**Status**: `planned`
**Priority**: medium
**Complexity**: medium

Detect when a component is discussed with increasing frequency — a signal of emerging problems or refactoring needs before they are explicitly raised.

Based on `discussion_count` trends in `files_discussed` over a 7/30-day sliding window. When a threshold is exceeded → automatically create a `research_question`: "Why is `{file_path}` being discussed so frequently?"

---

### Decision timeline

**Status**: `planned`
**Priority**: low
**Complexity**: low

A chronological view of all decisions per component or file. Implementable as an MCP tool:

```
decisions_timeline(file_path="src/auth/keycloak.py")
→ [2025-11: "Use Keycloak", 2026-01: "Add MFA", ...]
```

---

## Layer 3 — Knowledge graph

### Entity extraction → Neo4j graph

**Status**: `planned`
**Priority**: high
**Complexity**: high

BrainCell currently stores isolated records. The next step: extract entities (services, people, files, technologies) and their relationships, and store them in Neo4j (`ITL.ControlPlane.GraphDB`).

**Example graph:**
```
[Decision: "Use Keycloak"]
    ──depends_on──► [File: src/auth/keycloak.py]
    ──made_by──────► [Person: Niels]
    ──answers──────► [ResearchQuestion: "How do I authenticate users?"]
    ──contradicts──► [Decision: "Use JWT-only (2024)"]
```

This is the difference between an archive and a **knowledge network**.

**Relation types:**
| Relation | From → To |
|----------|-----------|
| `answers` | Decision → ResearchQuestion |
| `depends_on` | Decision → File |
| `made_by` | Decision → Person |
| `contradicts` | Decision → Decision |
| `references` | Snippet → File |
| `spawned` | Interaction → Decision/Question/Task |

---

### Impact analysis

**Status**: `planned`
**Priority**: medium
**Complexity**: high

"If I change this file, which decisions are affected?" → graph traversal across `files_discussed` ↔ `decisions` ↔ `architecture_notes`.

```
impact_analysis(file_path="src/auth/keycloak.py")
→ 3 decisions, 1 open question, 2 architecture notes affected
```

---

## Layer 4 — Proactive & predictive

### Proactive context push

**Status**: `planned`
**Priority**: high
**Complexity**: medium

BrainCell detects which file is open in the editor (via MCP), automatically retrieves relevant decisions, open questions, and snippets — and pushes them as context to the AI without being asked.

**Trigger:** `editor_context_changed(file_path)` → MCP event → BrainCell query → context response.

---

### Anomaly detection on interactions

**Status**: `planned`
**Priority**: low
**Complexity**: medium

If a session contains significantly more errors than average → automatically create a `high` priority `research_question`.

Based on a Z-score over a rolling average of `error` detections per session.

---

## Layer 5 — Multi-agent coordination

### BrainCell as shared working memory

**Status**: `planned`
**Priority**: high
**Complexity**: medium

In a multi-agent setup (`ITL.Agents`), each agent currently has its own context. With BrainCell as a central memory layer:

- Agent A makes a decision → BrainCell stores it
- Agent B picks up the decision on the next task
- No duplicate work, no conflicting choices

**Requires:** passing agent identity to `interactions_save` → `agent_id` field on `Interaction`.

---

### Agent handoff memory

**Status**: `planned`
**Priority**: medium
**Complexity**: medium

When an agent hands off a task to another agent, BrainCell automatically provides a `handoff_context`:

```
handoff_context(session_id, from_agent, to_agent)
→ {
    "decisions": [...],
    "open_questions": [...],
    "files_discussed": [...],
    "tasks_open": [...]
  }
```

---

## Layer 6 — Export & feedback loop

### Fine-tuning export (`memory_export` tool)

**Status**: `planned`
**Priority**: medium
**Complexity**: low

JSONL export in SFT format (Supervised Fine-Tuning), directly usable for LoRA fine-tuning:

```json
{"messages": [
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "..."}
]}
```

**Filters:** `quality_score`, `period`, `cell_types`, `min_confidence`.

```
memory_export(period="last_90_days", min_quality=0.7, format="jsonl")
```

---

### Human-in-the-loop feedback

**Status**: `planned`
**Priority**: medium
**Complexity**: low

```
feedback_save(interaction_id, rating=5, correction="A better approach would be...")
```

Ratings build a `quality_score` per interaction. Combined with `memory_export`: only highly-rated interactions feed into fine-tuning data.

---

## Priority overview

| Feature | Value | Complexity | Priority |
|---------|-------|------------|----------|
| Contradiction detection | ★★★★★ | Medium | high |
| Knowledge graph (Neo4j) | ★★★★★ | High | high |
| Proactive context push | ★★★★☆ | Medium | high |
| Multi-agent shared memory | ★★★★★ | Medium | high |
| Memory consolidation | ★★★★☆ | Medium | medium |
| Fine-tuning export | ★★★★☆ | Low | medium |
| Confidence scoring | ★★★☆☆ | Low | medium |
| Drift detection | ★★★★☆ | Medium | medium |
| Agent handoff memory | ★★★★☆ | Medium | medium |
| Time-travel queries | ★★★☆☆ | Low | low |
| Impact analysis | ★★★★☆ | High | low |
| Anomaly detection | ★★★☆☆ | Medium | low |
| Decision timeline | ★★★☆☆ | Low | low |
| Human feedback loop | ★★★★☆ | Low | medium |
