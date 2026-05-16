# 09 — Testing, Observability & Ops

> Part of the [P2P Offline-First Memory](./README.md) design series.

---

## 1. Test Matrix

### 1.1 Unit Tests

| Test area | File | What to test |
|-----------|------|-------------|
| `canonical_json_dumps` | `tests/test_canonical.py` | Key ordering, UTC times, no NaN |
| `EventEnvelope` serialisation | `tests/test_event_envelope.py` | Round-trip, field validation |
| `Policy` validation | `tests/test_policy.py` | Classification rank, required fields |
| `PolicyEngine` rules | `tests/test_policy_engine.py` | See table in [04 — Policy Engine](./04-policy-engine.md) §7 |
| `EventStore.append` | `tests/test_event_store.py` | Insert, duplicate idempotency |
| `EventStore.get_since` | `tests/test_event_store.py` | Cursor pagination, ordering |
| `DecisionsProjector` | `tests/test_projectors.py` | Created, archived, superseded |
| `FTS search` | `tests/test_search.py` | Keyword match, no-results, multi-table |
| Signature sign/verify | `tests/test_crypto.py` | Valid, tampered payload → FAIL |
| Bundle export structure | `tests/test_bundles.py` | Manifest fields, event count |
| Bundle import verification | `tests/test_bundles.py` | Valid, bad manifest sig, bad event sig |

### 1.2 Integration Tests

#### Scenario 1 — Single-node offline

```
1. Start node with no peers configured
2. Call interactions_save (10 items)
3. Call decisions_save (5 items)
4. Call search_memory("...")  → returns results from FTS
5. Call get_relevant_context("...") → returns merged results
6. Assert: no network calls made
```

#### Scenario 2 — Two-node replication

```
1. Start node A (EU/NL)
2. Start node B (EU/DE), configured to sync from A
3. On A: save 100 interactions events
4. Wait for sync cycle to complete (or trigger manually)
5. On B: query interactions → returns 100 items
6. Assert: B's event store has 100 events from A
7. Assert: B's projector views match A's
```

#### Scenario 3 — Policy: EU-only residency

```
1. Start node A (EU/NL) with 10 EU-only events
2. Start node C (US), attempt sync from A
3. Assert: sync session admitted
4. Assert: 0 events delivered to C (all EU-only)
5. Assert: A's policy audit log has 10 DENY entries for can_send
```

#### Scenario 4 — Policy: no-5eyes

```
1. Node A has 5 events with legal_domain=no-5eyes
2. Node GB (5-eyes) attempts sync
3. Assert: 0 events delivered to GB node
4. Assert: policy audit entries: "legal domain: no-5eyes policy, peer is 5-eyes node"
```

#### Scenario 5 — Courier bundle round-trip

```
1. Node A: export bundle (filter: may_transit=true, max_class=confidential)
2. Verify bundle manifest signature
3. Node B (air-gapped): import bundle
4. Assert: accepted events appear in B's projector views
5. Rerun import of same bundle → accepted count is 0 (idempotent)
```

#### Scenario 6 — Tampered event detection

```
1. Create valid event, append to store
2. Manually modify payload_json in SQLite
3. Attempt to sync to peer
4. Peer: verify_signature → FAIL
5. Assert: event goes to quarantine table
6. Assert: quarantine reason logged
```

#### Scenario 7 — Network partition then reconcile

```
1. Node A and B syncing normally
2. Disable network between A and B
3. On A: save 20 new events
4. On B: save 10 new events
5. Re-enable network
6. Wait for sync cycle
7. Assert: A has B's 10 events; B has A's 20 events
8. Assert: no duplicate event_ids on either node
```

---

## 2. Observability

### 2.1 Structured Logging

Use `structlog` (already a project dependency). All log entries are JSON:

```json
{
  "ts": "2026-04-26T14:00:00.123Z",
  "level": "info",
  "event": "sync_session_complete",
  "peer_id": "node-eu-prod-01",
  "events_sent": 48,
  "events_received": 12,
  "duration_ms": 320,
  "session_id": "<uuid>"
}
```

Key log events:

| Log event | Level | Description |
|-----------|-------|-------------|
| `event_appended` | debug | Event stored in EventStore |
| `event_duplicate` | debug | Duplicate event_id silently ignored |
| `event_quarantined` | error | Signature/hash failure |
| `policy_deny` | warning | Policy engine denied an operation |
| `sync_session_start` | info | Replication session begins |
| `sync_session_complete` | info | Replication session ends with counts |
| `sync_session_error` | error | Transport or protocol error |
| `peer_not_admitted` | warning | Handshake denied |
| `bundle_export_complete` | info | Bundle exported |
| `bundle_import_complete` | info | Bundle imported with counts |
| `key_revoked` | warning | Key revocation received from peer |

### 2.2 Prometheus Metrics

Expose at `GET /metrics` (Prometheus text format):

```
# HELP braincell_eventstore_size_events Total events in local EventStore
# TYPE braincell_eventstore_size_events gauge
braincell_eventstore_size_events 12432

# HELP braincell_replication_lag_events Estimated events behind per peer
# TYPE braincell_replication_lag_events gauge
braincell_replication_lag_events{peer="node-eu-prod-01"} 0
braincell_replication_lag_events{peer="node-de-staging-01"} 47

# HELP braincell_sync_sessions_total Total replication sessions
# TYPE braincell_sync_sessions_total counter
braincell_sync_sessions_total{peer="node-eu-prod-01",result="success"} 1842
braincell_sync_sessions_total{peer="node-eu-prod-01",result="error"} 3

# HELP braincell_policy_denials_total Total policy engine denials
# TYPE braincell_policy_denials_total counter
braincell_policy_denials_total{operation="can_send",reason="residency_violation"} 102
braincell_policy_denials_total{operation="can_send",reason="legal_domain_5eyes"} 56

# HELP braincell_events_quarantined_total Events quarantined due to integrity failure
# TYPE braincell_events_quarantined_total counter
braincell_events_quarantined_total{reason="invalid_signature"} 0
```

### 2.3 Health Endpoint

`GET /health` extended response:

```json
{
  "status": "ok",
  "node_id": "node-eu-prod-01",
  "eventstore": {
    "status": "ok",
    "event_count": 12432,
    "db_size_bytes": 24576000
  },
  "replication": {
    "peers": [
      {
        "peer_id": "node-de-staging-01",
        "status": "syncing",
        "last_sync_at": "2026-04-26T14:00:00Z",
        "lag_events": 0
      }
    ]
  },
  "policy_engine": {
    "status": "ok"
  },
  "search_index": {
    "status": "ok",
    "indexed_events": 12100
  }
}
```

---

## 3. Operational Guidance

### 3.1 Backup

```bash
# Backup EventStore (SQLite WAL-safe copy)
sqlite3 data/braincell_events.db ".backup data/backups/braincell_events_$(date +%Y%m%d).db"

# Backup keys (encrypted, off-node)
gpg --encrypt --recipient ops@itl.internal keys/ | \
  gpg-s3-upload s3://braincell-backups/keys/$(date +%Y%m%d)/
```

Schedule: daily full backup + WAL checkpoint.

### 3.2 Key Rotation Procedure

```bash
# 1. Generate new signing key
braincell-admin keys generate --type signing --output keys/node_signing_new.*

# 2. Add to active keys config (keep old key for verification of historical events)
# config/keys.yaml: add new key_id, mark as "active"

# 3. Restart node (picks up new key for signing)
systemctl restart braincell

# 4. After retention window of oldest event using old key:
braincell-admin keys retire --key-id node-signing-2025-01-01-abcd
```

### 3.3 Peer Allowlist Management

```bash
# Add new peer
braincell-admin peers add \
  --peer-id node-de-prod-02 \
  --endpoint https://braincell-de-prod-02.internal:9504 \
  --tls-fingerprint sha256:<hex>

# Remove peer (stops sync, removes from allowlist)
braincell-admin peers remove --peer-id node-de-prod-02

# List peers and their sync status
braincell-admin peers list
```

### 3.4 Rebuilding Projections

After a projector bug fix or schema change:

```bash
# Truncate all projector views and replay from EventStore
braincell-admin rebuild-projections --all

# Rebuild only decisions projector
braincell-admin rebuild-projections --projector decisions

# Dry-run: show what would be rebuilt
braincell-admin rebuild-projections --all --dry-run
```

### 3.5 Quarantine Management

```bash
# List quarantined events
braincell-admin quarantine list

# Inspect a specific quarantined event
braincell-admin quarantine inspect --event-id <uuid>

# Purge quarantined events older than 30 days
braincell-admin quarantine purge --older-than 30d
```

---

## 4. Chaos & Resilience Testing

Recommended automated chaos tests:

| Test | Method |
|------|--------|
| EventStore corruption recovery | Corrupt random bytes in DB; expect graceful error, not panic |
| Kill node mid-sync | SIGKILL during active sync session; verify cursor recovery on restart |
| Clock skew | Set node clock 1 h ahead; verify ordering still correct |
| Full disk | Fill data volume; verify graceful degradation (reject writes, log, health=degraded) |
| Certificate expiry | Let TLS cert expire; verify peer rejects connection with clear error |
| Large event flood | Push 100k events in rapid succession; verify no data loss |

---

*Next: [10 — Editions & Packaging](./10-editions-packaging.md)*
