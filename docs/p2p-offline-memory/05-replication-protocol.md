# 05 — Replication Protocol

> Part of the [P2P Offline-First Memory](./README.md) design series.

---

## 1. Transport Choices

### MVP (Phase 1)

- **HTTPS + mTLS** — simple, firewall-friendly, auditable.
- Peer list configured statically (`config/peers.yaml`).

### Later phases

- gRPC (bidirectional streaming for lower latency).
- libp2p with rendezvous discovery.

---

## 2. Peer Registry

```yaml
# config/peers.yaml
peers:
  - peer_id: "node-eu-prod-01"
    endpoint: "https://braincell-eu-prod-01.internal:9504"
    tls_fingerprint: "sha256:<hex>"    # pin peer cert
    sync_interval_seconds: 60
    enabled: true

  - peer_id: "node-de-staging-01"
    endpoint: "https://braincell-de-staging-01.internal:9504"
    tls_fingerprint: "sha256:<hex>"
    sync_interval_seconds: 300
    enabled: true
```

---

## 3. API Endpoints

All replication endpoints live under `/replication/` and require mTLS (no additional token auth; certificate is the identity).

### 3.1 `POST /replication/handshake`

Exchange node profiles and negotiate session parameters.

**Request:**
```json
{
  "node_profile": { "...": "NodeProfile object" },
  "protocol_version": "1"
}
```

**Response:**
```json
{
  "node_profile": { "...": "NodeProfile object" },
  "protocol_version": "1",
  "session_id": "<uuid>",
  "session_max_classification": "confidential",
  "admitted": true,
  "deny_reason": null
}
```

If `admitted=false`, no sync should proceed. Log the reason.

### 3.2 `POST /replication/sync`

Pull events from a peer since a cursor.

**Request:**
```json
{
  "session_id": "<uuid>",
  "since_cursor": {
    "occurred_at": "2026-04-25T00:00:00Z",
    "event_id": "<uuid>"
  },
  "limit": 200,
  "wanted_event_types": ["interactions.created", "decisions.created"],
  "wanted_scopes": ["org:itl", "peer-group:eu-prod"]
}
```

- `since_cursor`: null for first-ever sync (start from beginning).
- `wanted_event_types`: optional allowlist (sender still applies its own policy filter).
- `wanted_scopes`: optional hint for sender to pre-filter; sender must still apply full policy.

**Response:**
```json
{
  "session_id": "<uuid>",
  "events": [ { "...": "EventEnvelope" }, "..." ],
  "next_cursor": {
    "occurred_at": "2026-04-26T13:59:59Z",
    "event_id": "<uuid>"
  },
  "has_more": true
}
```

- `events`: 0..`limit` EventEnvelope objects, already policy-filtered by sender.
- `has_more`: if true, caller should issue another request with `next_cursor`.

### 3.3 `POST /replication/push`

Push events to a peer (optional — pull is sufficient for MVP).

**Request:**
```json
{
  "session_id": "<uuid>",
  "events": [ { "...": "EventEnvelope" }, "..." ]
}
```

**Response:**
```json
{
  "accepted": 198,
  "rejected": 2,
  "rejected_details": [
    { "event_id": "...", "reason": "policy: residency violation" }
  ]
}
```

---

## 4. Sender-Side Filtering

When handling a `/replication/sync` request, the sender:

```
1. Load peer_profile (from handshake cache or re-verify)
2. Gather candidate events:
   SELECT * FROM events
   WHERE occurred_at > since_cursor.occurred_at
      OR (occurred_at = since_cursor.occurred_at AND event_id > since_cursor.event_id)
   ORDER BY occurred_at ASC, event_id ASC
   LIMIT limit * 2   -- over-fetch to account for filtering

3. For each event:
   policy_engine.can_send(event, peer_profile) → if DENY, skip (and log)

4. Return up to `limit` events that passed, plus next_cursor
```

---

## 5. Receiver-Side Processing

When the replicator receives a batch from a peer:

```python
async def process_received_batch(
    events: list[EventEnvelope],
    peer_profile: NodeProfile,
    local_profile: NodeProfile,
    event_store: EventStore,
    projector_registry: ProjectorRegistry,
    policy_engine: PolicyEngine,
    search_index: SearchIndex,
) -> tuple[int, int]:
    accepted = 0
    rejected = 0
    for event in events:
        # 1. Signature verification
        if not verify_signature(event):
            log.warning("signature_invalid", event_id=event.event_id)
            rejected += 1
            continue

        # 2. Policy checks
        if not policy_engine.can_receive(event, peer_profile).allowed:
            rejected += 1
            continue
        if not policy_engine.can_store(event, local_profile).allowed:
            rejected += 1
            continue

        # 3. Append (idempotent)
        inserted = await event_store.append(event)
        if inserted:
            # 4. Project
            await projector_registry.dispatch(event)
            # 5. Index
            await search_index.index(event)
        accepted += 1

    return accepted, rejected
```

---

## 6. Background Sync Loop

```python
async def replication_loop(peer_config: PeerConfig):
    while True:
        try:
            await sync_with_peer(peer_config)
        except Exception as e:
            log.error("sync_error", peer=peer_config.peer_id, error=str(e))
        await asyncio.sleep(peer_config.sync_interval_seconds)
```

```python
async def sync_with_peer(peer: PeerConfig):
    # 1. Handshake (or use cached session)
    session = await handshake(peer)
    if not session.admitted:
        log.warning("peer_not_admitted", peer=peer.peer_id, reason=session.deny_reason)
        return

    # 2. Pull loop
    cursor = await event_store.get_peer_cursor(peer.peer_id)
    while True:
        resp = await http_client.post(
            f"{peer.endpoint}/replication/sync",
            json={"session_id": session.session_id, "since_cursor": cursor, "limit": 200},
        )
        await process_received_batch(resp.events, session.peer_profile, ...)
        await event_store.update_peer_cursor(peer.peer_id, resp.next_cursor)
        cursor = resp.next_cursor
        if not resp.has_more:
            break
```

---

## 7. Idempotency & Conflict Handling

| Scenario | Behaviour |
|----------|-----------|
| Same event received twice | `append` returns `False` (already present); no duplicate in DB |
| Two nodes create a "decision" independently | Two separate events exist; projector keeps both; UI shows both |
| Two nodes "update" the same record | Both update events exist; projector applies in `occurred_at` order (last writer wins per node) |
| Network partition then reconnect | Sync resumes from last cursor; all missing events replicated |

There are **no conflicts** at the event level — events are immutable and identified by `event_id`.  
Apparent "conflicts" in projector views are handled by event ordering.

---

## 8. Metrics & Health

Expose via `/health` and `/metrics` (Prometheus format):

| Metric | Type | Description |
|--------|------|-------------|
| `braincell_replication_lag_events{peer}` | Gauge | Estimated events behind per peer |
| `braincell_sync_sessions_total{peer,result}` | Counter | Successful/failed sync sessions |
| `braincell_events_sent_total{peer}` | Counter | Events sent to peers |
| `braincell_events_received_total{peer}` | Counter | Events received from peers |
| `braincell_policy_denials_total{operation,reason}` | Counter | Policy engine denials |
| `braincell_eventstore_size_events` | Gauge | Total event count in local store |

---

*Next: [06 — Air-Gap: Courier, Bundles & Diode](./06-airgap-courier-bundles-diode.md)*
