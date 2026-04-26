# 03 — EventStore, Projectors & Local Search

> Part of the [P2P Offline-First Memory](./README.md) design series.

---

## 1. EventStore

The EventStore is the **single source of truth** for all events on a node. It is an append-only SQLite database.

### 1.1 Database Location

```
data/braincell_events.db
```

Configurable via environment variable `BRAINCELL_EVENT_DB_PATH`.

### 1.2 SQLite Schema

```sql
-- Core events table
CREATE TABLE IF NOT EXISTS events (
    event_id         TEXT NOT NULL PRIMARY KEY,
    occurred_at      TEXT NOT NULL,          -- RFC 3339 UTC
    event_type       TEXT NOT NULL,
    node_id          TEXT NOT NULL,
    actor_id         TEXT,
    schema_version   INTEGER NOT NULL DEFAULT 1,
    policy_json      TEXT NOT NULL,          -- JSON serialisation of Policy
    payload_json     TEXT,                   -- NULL when encrypted
    payload_cipher   BLOB,                   -- NULL when plaintext
    payload_cipher_meta TEXT,               -- JSON; NULL when plaintext
    signature        BLOB NOT NULL,
    hash             BLOB,
    prev_hash        BLOB,
    ingested_at      TEXT NOT NULL           -- when this node received the event
);

CREATE INDEX IF NOT EXISTS idx_events_occurred  ON events (occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_type      ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_node      ON events (node_id);

-- Per-peer replication cursors
CREATE TABLE IF NOT EXISTS peer_cursors (
    peer_id          TEXT NOT NULL PRIMARY KEY,
    last_occurred_at TEXT,
    last_event_id    TEXT,
    updated_at       TEXT NOT NULL
);
```

### 1.3 Python Interface

```python
class EventStore(Protocol):

    async def append(self, event: EventEnvelope) -> bool:
        """
        Append an event.  Returns True if inserted, False if already present
        (idempotent by event_id).  Never raises on duplicate.
        """
        ...

    async def get_since(
        self,
        cursor: Cursor | None,
        limit: int = 100,
        event_types: list[str] | None = None,
    ) -> tuple[list[EventEnvelope], Cursor]:
        """
        Return up to `limit` events after cursor, plus the next cursor.
        If cursor is None, start from the beginning.
        """
        ...

    async def get_by_ids(self, ids: list[str]) -> list[EventEnvelope]:
        ...

    async def has(self, event_id: str) -> bool:
        ...

    async def update_peer_cursor(self, peer_id: str, cursor: Cursor) -> None:
        ...

    async def get_peer_cursor(self, peer_id: str) -> Cursor | None:
        ...
```

```python
@dataclass
class Cursor:
    occurred_at: str   # RFC 3339; exclusive lower bound
    event_id: str      # tie-break for same timestamp
```

### 1.4 Implementation Notes

- Use `aiosqlite` for async access.
- Wrap `append` in a `BEGIN IMMEDIATE` transaction; use `INSERT OR IGNORE` semantics.
- Keep WAL mode enabled: `PRAGMA journal_mode=WAL`.
- Run `PRAGMA foreign_keys=ON` and `PRAGMA synchronous=NORMAL` for balanced durability.
- Never `UPDATE` or `DELETE` existing event rows.

---

## 2. Projectors

Projectors translate the event stream into **materialised views** that feed the existing cell APIs. This preserves the external API surface with no changes required in route handlers.

### 2.1 Design Principles

- Each projector handles one or more event types.
- Projectors are called synchronously in the write path (after `event_store.append` succeeds).
- A projector must be **idempotent** — replaying an event must produce the same state.
- Projectors maintain their own SQLite tables (can be in the same DB or a separate `braincell_views.db`).

### 2.2 Projector Interface

```python
class Projector(Protocol):
    event_types: list[str]

    async def handle(self, event: EventEnvelope) -> None:
        """Apply this event to the materialised view. Must be idempotent."""
        ...
```

### 2.3 ProjectorRegistry

```python
class ProjectorRegistry:
    def __init__(self):
        self._projectors: dict[str, list[Projector]] = {}

    def register(self, projector: Projector) -> None:
        for et in projector.event_types:
            self._projectors.setdefault(et, []).append(projector)

    async def dispatch(self, event: EventEnvelope) -> None:
        for proj in self._projectors.get(event.event_type, []):
            await proj.handle(event)
```

### 2.4 Example: DecisionsProjector

```python
class DecisionsProjector:
    event_types = ["decisions.created", "decisions.archived", "decisions.superseded"]

    async def handle(self, event: EventEnvelope) -> None:
        payload = event.payload or {}
        if event.event_type == "decisions.created":
            await db.execute(
                """
                INSERT OR IGNORE INTO decisions
                    (id, title, rationale, status, created_at, event_id)
                VALUES (?, ?, ?, 'active', ?, ?)
                """,
                (
                    payload.get("id"),
                    payload.get("title"),
                    payload.get("rationale"),
                    event.occurred_at,
                    event.event_id,
                ),
            )
        elif event.event_type == "decisions.archived":
            await db.execute(
                "UPDATE decisions SET status='archived' WHERE id=?",
                (payload.get("id"),),
            )
        elif event.event_type == "decisions.superseded":
            await db.execute(
                "UPDATE decisions SET status='superseded', superseded_by=? WHERE id=?",
                (payload.get("superseded_by"), payload.get("id")),
            )
```

### 2.5 Handling "Updates"

There are **no in-place edits** at the event level.  
Any change is a new event:

| Old model | Event-based equivalent |
|-----------|----------------------|
| `UPDATE decisions SET status='archived'` | Emit `decisions.archived` event |
| `UPDATE snippets SET body=…` | Emit `snippets.revised` event |
| `DELETE tasks WHERE id=…` | Emit `tasks.deleted` event |

The projector applies the latest state by event ordering (`occurred_at` + `event_id`).

### 2.6 Rebuilding Projections

Because the EventStore is append-only, projections can always be rebuilt from scratch:

```bash
# Truncate all view tables, then replay all events
braincell-admin rebuild-projections --from-beginning
```

This is useful after projector logic changes.

---

## 3. Local Search (FTS5)

### 3.1 Design

The local search index uses **SQLite FTS5** virtual tables. This provides keyword and phrase search without requiring Weaviate or any network access.

FTS tables live in the same database as projector views (or a dedicated `braincell_search.db`).

### 3.2 FTS Schema

```sql
-- decisions full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS fts_decisions USING fts5(
    title,
    rationale,
    tags,
    content='decisions',
    content_rowid='rowid',
    tokenize='unicode61'
);

-- interactions
CREATE VIRTUAL TABLE IF NOT EXISTS fts_interactions USING fts5(
    summary,
    outcome,
    tags,
    content='interactions',
    content_rowid='rowid',
    tokenize='unicode61'
);

-- conversations
CREATE VIRTUAL TABLE IF NOT EXISTS fts_conversations USING fts5(
    topic,
    summary,
    tags,
    content='conversations',
    content_rowid='rowid',
    tokenize='unicode61'
);

-- notes
CREATE VIRTUAL TABLE IF NOT EXISTS fts_notes USING fts5(
    title,
    body,
    tags,
    content='notes',
    content_rowid='rowid',
    tokenize='unicode61'
);
```

### 3.3 Keeping the Index Up-to-Date

Use SQLite triggers to keep FTS tables in sync with the content tables updated by projectors:

```sql
-- Example for decisions
CREATE TRIGGER fts_decisions_insert AFTER INSERT ON decisions BEGIN
    INSERT INTO fts_decisions(rowid, title, rationale, tags)
    VALUES (new.rowid, new.title, new.rationale, new.tags);
END;

CREATE TRIGGER fts_decisions_update AFTER UPDATE ON decisions BEGIN
    INSERT INTO fts_decisions(fts_decisions, rowid, title, rationale, tags)
    VALUES ('delete', old.rowid, old.title, old.rationale, old.tags);
    INSERT INTO fts_decisions(rowid, title, rationale, tags)
    VALUES (new.rowid, new.title, new.rationale, new.tags);
END;

CREATE TRIGGER fts_decisions_delete AFTER DELETE ON decisions BEGIN
    INSERT INTO fts_decisions(fts_decisions, rowid, title, rationale, tags)
    VALUES ('delete', old.rowid, old.title, old.rationale, old.tags);
END;
```

Alternatively, the projector can update FTS tables explicitly, which gives more control over what is indexed.

### 3.4 Search API

```python
async def search_memory(
    query: str,
    cell_types: list[str] | None = None,  # filter to specific cells
    limit: int = 20,
    since: str | None = None,
) -> list[SearchResult]:
    """
    Run BM25-ranked FTS5 query across all enabled FTS tables.
    Returns results from most relevant to least relevant.
    """
    ...
```

MCP tool mapping: `search_memory` → calls this function.

### 3.5 `get_relevant_context`

```python
async def get_relevant_context(
    context_hint: str,
    limit: int = 10,
) -> list[SearchResult]:
    """
    Combines:
      1. FTS search on context_hint
      2. Recent items from projector views (last N by occurred_at)
    Returns merged, deduplicated, ranked list.
    """
    fts_results = await search_memory(context_hint, limit=limit * 2)
    recent = await get_recent_items(limit=limit)
    return rank_and_merge(fts_results, recent, limit=limit)
```

### 3.6 Optional: Local Embeddings (Later Phase)

Phase 2 can add local embedding-based search:

1. Compute embeddings with a small local model (e.g. `sentence-transformers/all-MiniLM-L6-v2`).
2. Store in a FAISS index file (`data/braincell_vectors.faiss`).
3. Combine ANN results with FTS results in `get_relevant_context`.

**Do not block MVP on this.**

---

*Next: [04 — Policy Engine](./04-policy-engine.md)*
