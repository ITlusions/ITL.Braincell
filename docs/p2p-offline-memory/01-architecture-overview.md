# 01 — Architecture Overview

> Part of the [P2P Offline-First Memory](./README.md) design series.

---

## 1. Goals

| # | Goal |
|---|------|
| G1 | **Local-first writes** — every `*_save` tool call succeeds without network access |
| G2 | **P2P replication** — events are exchanged with filtering based on policy and node profile |
| G3 | **Data residency** — events are never stored/received/sent where not permitted |
| G4 | **Air-gap support** — courier node and signed replication bundles |
| G5 | **Preserve external API surface** — `/tools/*` (MCP) and `/api/*` (REST) continue to work |
| G6 | **Auditable provenance** — every event is signed and optionally hash-chained |

## 2. Non-Goals (MVP)

- Global consistent search across all nodes (each node searches only what it stores).
- Real-time collaborative editing / CRDT (updates are modelled as new events).
- Auto-discovery via libp2p (MVP uses a configured peer list; libp2p is a later phase).

---

## 3. Node Components

```mermaid
flowchart TB
    subgraph node["BrainCell Node"]
        direction TB
        TL["Tools / Cells Layer\n(existing)"]
        PE["Policy Engine\n(admission, send/recv)"]
        ES["Event Store\n(SQLite append-only)"]
        PR["Projectors\n(mat. views)"]
        FI["Local FTS5 idx"]
        RE["Replicator\n(P2P)"]
        TL --> PE
        TL --> ES
        PE --> ES
        ES --> PR
        ES --> FI
        ES --> RE
    end
    PEERS["Peer Nodes /\nCourier / Bundles"]
    RE --> PEERS
```

### Component responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Tools / Cells Layer** | Existing cell code. Intercepts writes to produce events. |
| **Policy Engine** | Evaluates `can_store`, `can_send`, `can_receive` for every event. |
| **Event Store** | Append-only SQLite log. Single source of truth for all events on this node. |
| **Projectors** | Translate event stream into materialised "memory tables" consumed by existing APIs. |
| **Local FTS Index** | SQLite FTS5 virtual tables for keyword/tag search without central Weaviate. |
| **Replicator** | Cursor-based sync over mTLS HTTP/gRPC; manages peer registry and cursors. |

---

## 4. Write-Path Data Flow

```mermaid
flowchart TD
    A["Tool invoked\n(e.g. interactions_save)"]
    B["Assign default policy\n(if caller did not provide one)"]
    C["Build EventEnvelope\n(event_id, type, actor, payload, policy)"]
    D["Sign envelope (Ed25519)"]
    E{"Policy Engine:\ncan_store(event, local_profile)?"}
    F["Reject with policy error"]
    G["Append to EventStore (idempotent)"]
    H["Projector(s) update local views"]
    I["FTS index update"]
    J["Replicator: eventually sync to allowed peers"]
    K["Return success to caller"]

    A --> B --> C --> D --> E
    E -- NO --> F
    E -- YES --> G
    G --> H
    G --> I
    G --> J --> K
```

---

## 5. Read-Path Data Flow

```mermaid
flowchart TD
    A["Tool invoked\n(e.g. search_memory, get_relevant_context)"]
    B["Query Local FTS Index\n(fast, deterministic)"]
    C["Merge with recent items\nfrom Projector views"]
    D["Apply result policy filter\n(strip payloads caller is not permitted to see)"]
    E["Return results"]

    A --> B --> C --> D --> E
```

---

## 6. Replication Data Flow

```mermaid
flowchart TD
    A["Replicator background loop\n(per configured peer)"]
    B["POST /replication/handshake\n(exchange NodeProfiles)"]
    C["POST /replication/sync\n(since=last_cursor, limit=N)"]
    D["Remote sends filtered\nEventEnvelope batch"]
    E["Verify signature"]
    F{"can_receive +\ncan_store?"}
    G["Discard event"]
    H["append / project / index"]
    I["Update peer cursor"]
    J["Sleep(backoff)"]

    A --> B --> C --> D --> E --> F
    F -- NO --> G
    F -- YES --> H --> I --> J --> A
```

---

## 7. Deployment Topologies

### 7.1 Single-node (offline/edge)

```mermaid
graph LR
    N["BrainCell Node\n(offline / edge — no peers configured)"]
    style N fill:#dae8fc,stroke:#6c8ebf
```

### 7.2 Two-node direct sync

```mermaid
graph LR
    A["Node A"] <-- "mTLS sync" --> B["Node B"]
```

### 7.3 Hub-and-spoke

```mermaid
graph TB
    Hub["Hub / Central"]
    A["Node A"]
    B["Node B"]
    C["Node C"]
    D["Node D"]
    A <--> Hub
    B <--> Hub
    C <--> Hub
    D <--> Hub
```

Hub is just another peer with wider policy permissions (can store more, can relay).

### 7.4 Air-gapped site

```mermaid
graph LR
    CN["Connected Node"]
    CL["Courier Laptop\n(physically transported)"]
    AG["Air-Gapped Node"]
    CN -- "bundle export" --> CL
    CL -- "physical transport" --> AG
```

---

## 8. Integration Strategy with Existing Code

The existing Cells Layer writes to PostgreSQL and Weaviate. The integration adds an **event hook** into each relevant cell's write path:

```python
# Existing (simplified)
async def save_interaction(data):
    record = await db.save(InteractionModel(**data))
    return record

# With event hook
async def save_interaction(data):
    record = await db.save(InteractionModel(**data))          # keep for compat
    event = build_event("interactions.created", data, policy=default_policy())
    await event_store.append(event)                           # new
    return record
```

Cells to migrate first (highest value):
1. `src/cells/interactions/cell.py`
2. `src/cells/decisions/cell.py`

Later phases: all remaining cells.

---

*Next: [02 — Data Model](./02-data-model-events-policy-nodeprofile.md)*
