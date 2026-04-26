# 12 — FAQ & Glossary

> Part of the [P2P Offline-First Memory](./README.md) design series.

---

## Frequently Asked Questions

### General

**Q: What problem does BrainCell P2P solve that a central database does not?**

A central database creates a single point of failure and a single jurisdiction. BrainCell P2P allows agents to continue working when the central service is unavailable (network outage, maintenance, air-gap), and enforces residency rules so that sensitive data never travels outside its permitted jurisdiction — by architecture, not by policy document.

---

**Q: Is this a CRDT / real-time collaboration system?**

No. BrainCell uses an **event-sourced append-only log**. There is no real-time conflict resolution. "Updates" are new events; the projector applies them in time order (last-writer-wins per node). This is simpler and more auditable than CRDT for the primary use cases (operational memory, decisions, incidents).

---

**Q: Can two nodes independently modify the same record?**

Each node can emit update events for any record. Both events will eventually be replicated. The projector resolves the final view by `occurred_at` ordering. If two nodes simultaneously "archive" the same decision, both events exist in the log — the projector applies the last one. This is intentional: the history is preserved.

---

**Q: What happens to data that was in PostgreSQL/Weaviate before the P2P system?**

The migration ticket T1 includes a `braincell-admin migrate-eventstore` command that reads existing rows from PostgreSQL and emits `*.created` events for each, bootstrapping the EventStore from historical data. Weaviate vectors are not migrated (they will be rebuilt from FTS5 or by re-indexing).

---

### Policy & Compliance

**Q: What is "5-eyes" in this context?**

The "Five Eyes" intelligence alliance comprises: United States (US), United Kingdom (GB), Canada (CA), Australia (AU), and New Zealand (NZ). In BrainCell, setting `legal_domain=no-5eyes` on a policy means that event must never be stored on or transmitted to nodes with `jurisdiction` in any of those countries.

---

**Q: Can a node forge its NodeProfile to appear to be in a different jurisdiction?**

The NodeProfile is signed by the node's own key (and optionally by an org CA). A malicious node can claim any jurisdiction in its profile, but it cannot forge the org CA signature. For strict enforcement, use org CA signing and verify `profile_signature` against the CA public key during handshake. For additional assurance, combine with IP geolocation and TLS certificate subject field checks (belt-and-suspenders).

---

**Q: What happens if a policy configuration is wrong and events get replicated somewhere they shouldn't?**

The EventStore is append-only and all events carry their `policy` at the time of creation. A policy misconfiguration does not retroactively change stored events. To remediate:
1. Fix the policy configuration.
2. The misdirected events cannot be "un-sent" but can be deleted from the receiving node by the operator if legally required.
3. Add an audit alert so future misconfigurations are caught at the boundary (policy deny logs).

---

**Q: How is GDPR "right to erasure" handled in an append-only event log?**

Options:
1. **Payload encryption by scope** (preferred): Encrypt the payload with a scope key. To erase, delete the scope private key. The event record remains but the payload becomes unreadable.
2. **Redaction event**: Emit a `<cell>.redacted` event containing only the `event_id` to redact. Projectors remove the data from views. The original event envelope (minus payload) remains for audit.
3. **Soft delete from views**: Only the projector view is cleared; the event log retains the record for audit purposes. This satisfies most GDPR requests where the controller can demonstrate the data is no longer accessible.

Consult your legal team for the appropriate approach.

---

### Replication & Air-Gap

**Q: What if a peer is offline during sync? Will I lose data?**

No. The Replicator uses cursor-based sync. When the peer comes back online, it resumes from where it left off. Events are never deleted from the EventStore during the retention window, so nothing is lost due to temporary offline periods.

---

**Q: How large can a replication bundle be?**

Configurable via `max_bundle_size_bytes`. Default is 100 MB. For physical media (USB), set to the media capacity (e.g., 4 GB). Bundles are split into chunks automatically if configured. There is no hard upper limit; it is bounded by available disk space and transfer time.

---

**Q: Can I use bundles AND live replication on the same node?**

Yes. They use the same EventStore and policy engine. A node can simultaneously:
- Sync continuously with online peers via P2P.
- Export bundles for air-gapped sites.
- Import bundles from other air-gapped sites.

All operations are idempotent and use the same cursor/event_id deduplication.

---

**Q: What happens if a bundle is intercepted in transit?**

If the payload is encrypted (`payload_mode=team` or `org`), the intercepted bundle is unreadable without the scope private key. The bundle manifest and event signatures remain intact, so any tampering with the bundle content is detected on import. For highly sensitive data, always ensure `classification >= confidential` events use payload encryption before transit.

---

### Performance

**Q: How many events can the SQLite EventStore handle?**

SQLite with WAL mode comfortably handles millions of rows. At 1 KB per event (typical for BrainCell), 10 million events ≈ 10 GB. Performance degrades at several hundred MB/s write throughput but that far exceeds BrainCell's expected write rates. If you exceed ~50 million events on a single node, consider archiving older events to cold storage and keeping a rolling window in the hot EventStore.

---

**Q: Is the FTS5 search fast enough for production?**

For up to ~1 million indexed documents on commodity hardware, FTS5 returns results in < 50 ms. Beyond that, consider adding a local embedding model for semantic ranking (Phase 2), or pre-filtering by `event_type` or `occurred_at` range before full-text search.

---

## Glossary

| Term | Definition |
|------|-----------|
| **Actor** | The user or agent identity that created an event (`actor_id`). |
| **Air-gap** | Physical network isolation preventing electronic data transfer. BrainCell supports air-gapped operation via bundles. |
| **Append-only log** | A data structure where records can only be added, never modified or deleted. BrainCell's EventStore is append-only. |
| **Bundle** | A signed, self-contained archive of EventEnvelope objects for physical or offline transfer. |
| **Canonical JSON** | A deterministic JSON serialisation with sorted keys and normalised formatting, required for consistent signing. |
| **Cell** | A self-contained memory domain in BrainCell (e.g., `decisions`, `interactions`). See `src/cells/`. |
| **Chunk** | A fixed-size part of a large bundle, used for transfer over constrained media. |
| **Classification** | The sensitivity level of an event's payload: `public`, `internal`, `confidential`, `restricted`. |
| **Courier node** | A node with `role=courier` that physically transports events between networks. |
| **Cursor** | A `(occurred_at, event_id)` pair marking the last-seen position in the EventStore, used for incremental sync. |
| **DEK** | Data Encryption Key — a random symmetric key used to encrypt a single event payload. |
| **Derived domain** | A boolean attribute computed from `jurisdiction` (e.g., `EU=true`, `5eyes=false`). |
| **Diode-in** | A node role that accepts event imports but never exports. |
| **Diode-out** | A node role that exports events but never accepts imports. |
| **Ed25519** | An elliptic-curve digital signature algorithm used to sign EventEnvelopes. |
| **Event** | An immutable record of something that happened, stored as an EventEnvelope. |
| **EventEnvelope** | The canonical data structure for an event, including identity, policy, payload, and cryptographic fields. |
| **EventStore** | The append-only SQLite database storing all EventEnvelopes on a node. |
| **FTS5** | SQLite's Full-Text Search extension (version 5). Used for local keyword search. |
| **Handshake** | The initial exchange of NodeProfiles between two peers, resulting in session establishment or denial. |
| **Idempotent** | An operation that produces the same result when applied multiple times. BrainCell's append and import operations are idempotent. |
| **Jurisdiction** | The country/region where a node physically operates (ISO 3166-1 alpha-2, e.g. `NL`). |
| **KEK** | Key Encryption Key — derived via ECDH, used to wrap the DEK. |
| **Legal domain** | A named rule set governing cross-border data flow (e.g., `no-5eyes`, `eu-gdpr`). |
| **Local-first** | A design principle where all writes succeed locally without network access, and are synchronised when connectivity is available. |
| **Manifest** | The metadata file in a bundle describing its contents, cursor range, and event hashes. |
| **may_transit** | A policy flag allowing an event to be included in courier/bundle transfers even if not directly replicable. |
| **mTLS** | Mutual TLS — both client and server authenticate with certificates. Used for all P2P connections. |
| **NodeProfile** | A signed declaration of a node's identity, jurisdiction, groups, capabilities, and public keys. |
| **P2P** | Peer-to-peer — direct node-to-node communication without a central relay. |
| **Payload encryption** | Encrypting the event payload with a scope key so only authorised key holders can read it. |
| **Peer registry** | The configured list of known peers (`config/peers.yaml`). |
| **Policy** | A structured set of rules (classification, residency, legal_domain, sharing_scope, retention, may_transit) attached to every event. |
| **Policy Engine** | The component that evaluates `can_store`, `can_send`, `can_receive`, and `admit_peer` decisions. |
| **Projector** | A component that translates events from the EventStore into materialised view tables consumed by existing APIs. |
| **Quarantine** | A table holding events that failed signature verification or policy checks; never included in normal views. |
| **Residency** | The allowed geographic location(s) for storing an event (e.g., `EU`, `NL`, `GLOBAL`). |
| **Retention** | How long (in days) an event must be kept. `0` = indefinite. |
| **Sharing scope** | Who may receive an event: `local-only`, `org:<id>`, `team:<id>`, `peer-group:<id>`, `public`. |
| **WAL** | Write-Ahead Log — SQLite journal mode for better concurrency and durability. Enabled by default. |
| **X25519** | An elliptic-curve Diffie-Hellman function used for key agreement in payload encryption. |

---

*End of P2P Offline-First Memory documentation bundle.*  
*Return to: [README](./README.md)*
