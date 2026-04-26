# ITL.BrainCell — P2P Offline-First Memory System

> **Status:** Design / Pre-Implementation  
> **Date:** 2026-04-26  
> **Audience:** Developers implementing the BrainCell distributed memory layer

---

## What This Document Set Covers

This bundle specifies how to implement a **decentralised, offline-first, policy-governed memory system** for BrainCell. When fully built, BrainCell will:

- Replicate memory between nodes over P2P links (and "courier" air-gap bundles).
- Enforce **where data may live** (residency/jurisdiction, 5-eyes-like constraints, team/org scopes).
- Continue operating **when central infrastructure is unavailable** (local-first).
- Provide **local search** without requiring central Weaviate (FTS5 baseline; embeddings optional).
- Guarantee **integrity and provenance** via event signing; confidentiality via scope-based encryption.

---

## One-Line Positioning

> *BrainCell is a policy-governed, offline-first, peer-to-peer memory layer for agents — built for regulated and disconnected operations.*

---

## Document Index

| # | File | Topic |
|---|------|-------|
| 01 | [Architecture Overview](./01-architecture-overview.md) | Goals, non-goals, component diagram, data-flow |
| 02 | [Data Model — Events, Policy, NodeProfile](./02-data-model-events-policy-nodeprofile.md) | EventEnvelope, Policy object, NodeProfile schema |
| 03 | [EventStore, Projectors & Search](./03-eventstore-projectors-search.md) | SQLite schema, Projector design, FTS5 local search |
| 04 | [Policy Engine](./04-policy-engine.md) | Admission, send/receive/store rules, residency mapping |
| 05 | [Replication Protocol](./05-replication-protocol.md) | Handshake, cursor sync, filtering, idempotency |
| 06 | [Air-Gap — Courier, Bundles & Diode](./06-airgap-courier-bundles-diode.md) | Export/import bundles, courier node, data-diode policy |
| 07 | [Media-Aware Transfer](./07-media-aware-transfer.md) | Binary payloads, chunking, checksums, bandwidth controls |
| 08 | [Security, Crypto & Identity](./08-security-crypto-identity.md) | mTLS, Ed25519 signing, scope encryption, key rotation |
| 09 | [Testing, Observability & Ops](./09-testing-observability-ops.md) | Test matrix, metrics, audit logs, health endpoints |
| 10 | [Editions & Packaging](./10-editions-packaging.md) | Community vs Enterprise features, deployment variants |
| 11 | [Rollout Roadmap](./11-rollout-roadmap.md) | Phased ticket breakdown (T1–T8) |
| 12 | [FAQ & Glossary](./12-faq-glossary.md) | Frequently asked questions, term definitions |

---

## Quick Start for Developers

1. Read **[01 — Architecture Overview](./01-architecture-overview.md)** to understand the overall design.
2. Read **[02 — Data Model](./02-data-model-events-policy-nodeprofile.md)** before touching any code — it is the contract everything else builds on.
3. Implement tickets in the order from **[11 — Rollout Roadmap](./11-rollout-roadmap.md)** (T1 → T2 → T3 → …).
4. Run the test matrix from **[09 — Testing](./09-testing-observability-ops.md)** after each ticket.

---

## Core Design Principles

| Principle | Implication |
|-----------|-------------|
| **Local-first** | Every write succeeds without network access |
| **Append-only events** | No in-place edits; updates are new events |
| **Policy at the boundary** | Every send/receive/store decision is evaluated against policy |
| **Signed provenance** | Every event carries a verifiable signature |
| **Idempotent sync** | Replaying the same event is safe |

---

## Related Docs

- [API Architecture](../api/ARCHITECTURE.md)
- [API Endpoints](../api/ENDPOINTS.md)
- [MCP Guide](../mcp/GUIDE.md)
- [Roadmap](../roadmap/README.md)
