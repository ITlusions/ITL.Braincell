# 02 — Data Model: Events, Policy & NodeProfile

> Part of the [P2P Offline-First Memory](./README.md) design series.

---

## 1. EventEnvelope

All replication and local storage is done as **EventEnvelope** objects. This is the canonical, immutable unit of data.

### 1.1 Schema

```python
@dataclass
class EventEnvelope:
    # Identity
    event_id: str           # UUID v4
    event_type: str         # e.g. "interactions.created", "decisions.archived"
    occurred_at: str        # RFC 3339, always UTC, e.g. "2026-04-26T14:00:00Z"
    schema_version: int     # incremented when payload schema changes

    # Origin
    node_id: str            # node that originally created this event
    actor_id: str           # user or agent identity

    # Policy
    policy: Policy          # see section 2

    # Payload — exactly one of plaintext or ciphertext is set
    payload: dict | None          # JSON-serialisable plaintext
    payload_cipher: bytes | None  # encrypted payload bytes
    payload_cipher_meta: dict | None  # algorithm, nonce, wrapped DEK, key_id

    # Integrity
    signature: bytes        # Ed25519 sig over canonical_json(envelope minus signature)
    hash: bytes | None      # SHA-256 of canonical_json(envelope minus hash+signature)
    prev_hash: bytes | None # hash of previous event from same node (tamper-evident chain)
```

### 1.2 Event Types (initial set)

| Event type | Payload cell |
|------------|-------------|
| `interactions.created` | interactions |
| `interactions.archived` | interactions |
| `decisions.created` | decisions |
| `decisions.superseded` | decisions |
| `decisions.archived` | decisions |
| `conversations.created` | conversations |
| `snippets.created` | snippets |
| `tasks.created` | tasks |
| `tasks.completed` | tasks |
| `errors.created` | errors |
| `notes.created` | notes |
| `incidents.created` | incidents |
| `intel_reports.created` | intel_reports |

> New cells add new event types following the `<cell>.<verb>` convention.

### 1.3 Canonical Serialisation

Define `canonical_json_dumps(obj: dict) -> str`:

```python
import json

def canonical_json_dumps(obj: dict) -> str:
    """Deterministic JSON: sorted keys, compact separators, UTC timestamps."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
```

Rules:
- Keys always sorted alphabetically (recursive).
- No trailing whitespace.
- All timestamps in ISO 8601 UTC (`Z` suffix).
- No `NaN` / `Infinity` floats (use strings or nulls).
- The `signature` field is **excluded** when signing.
- The `hash` field is **excluded** when computing the hash.

---

## 2. Policy Object

The `Policy` object travels with every event and constrains where it may be stored, transmitted, and by whom.

### 2.1 Schema

```python
@dataclass
class Policy:
    classification: Literal["public", "internal", "confidential", "restricted"]
    residency: str               # "GLOBAL" | ISO 3166-1 alpha-2 | region ("EU", "US")
    legal_domain: str            # "no-5eyes" | "5eyes-ok" | "eu-gdpr" | custom label
    sharing_scope: str           # see section 2.2
    retention_days: int          # 0 = indefinite
    may_transit: bool            # courier/bundle transit allowed even if not may_store
```

### 2.2 `sharing_scope` Values

| Value | Meaning |
|-------|---------|
| `local-only` | Never replicate; stay on originating node |
| `org:<org_id>` | Replicate to any node within the same org |
| `team:<team_id>` | Replicate only to nodes in the named team group |
| `peer-group:<group_id>` | Replicate only to nodes explicitly in the named peer group |
| `public` | No scope restriction (subject to residency/legal_domain) |

### 2.3 Example Policies

**EU internal, shared within org**
```json
{
  "classification": "internal",
  "residency": "EU",
  "legal_domain": "no-5eyes",
  "sharing_scope": "org:itl",
  "retention_days": 365,
  "may_transit": true
}
```

**Restricted — stays on originating node**
```json
{
  "classification": "restricted",
  "residency": "NL",
  "legal_domain": "no-5eyes",
  "sharing_scope": "local-only",
  "retention_days": 30,
  "may_transit": false
}
```

**Air-gap exportable digest (no secrets in payload)**
```json
{
  "classification": "internal",
  "residency": "EU",
  "legal_domain": "no-5eyes",
  "sharing_scope": "peer-group:airgap-export",
  "retention_days": 90,
  "may_transit": true
}
```

### 2.4 Default Policies Per Cell

Each cell provides defaults. Callers may override with stricter values; relaxation requires a privilege flag.

| Cell | classification | residency | legal_domain | sharing_scope | retention_days |
|------|---------------|-----------|--------------|---------------|----------------|
| interactions | internal | EU | no-5eyes | org:itl | 30 |
| decisions | internal | EU | no-5eyes | org:itl | 365 |
| conversations | internal | EU | no-5eyes | org:itl | 90 |
| snippets | internal | GLOBAL | 5eyes-ok | org:itl | 0 |
| notes | internal | EU | no-5eyes | org:itl | 365 |
| tasks | internal | EU | no-5eyes | team:default | 365 |
| errors | internal | EU | no-5eyes | org:itl | 90 |
| incidents | confidential | EU | no-5eyes | team:sre | 730 |
| intel_reports | confidential | EU | no-5eyes | team:security | 730 |

---

## 3. NodeProfile

A `NodeProfile` is shared during peer handshake. It describes the physical and administrative properties of a node and is used by the Policy Engine to make admission and send/receive decisions.

### 3.1 Schema

```python
@dataclass
class NodeProfile:
    # Identity
    node_id: str                # UUID or FQDN-based stable ID
    org_id: str
    jurisdiction: str           # ISO 3166-1 alpha-2, e.g. "NL", "DE", "US"

    # Derived policy labels (computed from jurisdiction + config)
    derived_domains: dict       # e.g. {"EU": true, "5eyes": false, "nato": true}

    # Group membership
    groups: list[str]           # e.g. ["team:sre", "peer-group:eu-prod"]

    # Role
    role: Literal["normal", "courier", "central", "diode-out", "diode-in"]

    # Capabilities
    capabilities: NodeCapabilities

    # Public keys
    signing_public_key: str     # base64url Ed25519 public key
    encryption_public_key: str  # base64url X25519 public key (for scope encryption)

    # Trust anchor
    profile_signature: str      # signed by node identity key or org CA
    profile_signed_at: str      # RFC 3339
```

```python
@dataclass
class NodeCapabilities:
    can_store_restricted: bool  # TPM or equivalent hardware backing required
    has_tpm: bool
    max_classification: Literal["public", "internal", "confidential", "restricted"]
    supported_payload_modes: list[str]  # ["none", "device", "team", "org"]
```

### 3.2 Derived Domain Computation

```python
FIVE_EYES = {"US", "GB", "CA", "AU", "NZ"}
EU_MEMBERS = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
    "NL", "PL", "PT", "RO", "SE", "SI", "SK"
}

def compute_derived_domains(jurisdiction: str) -> dict:
    return {
        "EU": jurisdiction in EU_MEMBERS,
        "5eyes": jurisdiction in FIVE_EYES,
        "nato": jurisdiction in NATO_MEMBERS,   # define similarly
    }
```

### 3.3 NodeProfile Verification

On receipt of a NodeProfile from a peer:

1. Verify `profile_signature` against the node's own `signing_public_key`.
2. Optionally verify against an org CA cert if cross-org trust is configured.
3. Reject if signature invalid or `profile_signed_at` is older than configured TTL (default 24 h).
4. Cache verified profile; re-verify on TTL expiry or re-handshake.

---

## 4. `payload_cipher_meta` Structure

When a payload is encrypted, `payload_cipher_meta` carries everything needed to decrypt:

```json
{
  "algorithm": "chacha20-poly1305",
  "nonce": "<base64url>",
  "dek_wrapped": "<base64url>",
  "key_id": "<scope-key-identifier>",
  "scope": "team:sre"
}
```

Fields:

| Field | Description |
|-------|-------------|
| `algorithm` | Symmetric algorithm used on DEK (e.g. `aes-256-gcm`, `chacha20-poly1305`) |
| `nonce` | Random nonce used for symmetric encryption |
| `dek_wrapped` | DEK encrypted with scope public key (X25519 ECDH + KDF) |
| `key_id` | Identifier of the scope key used to wrap DEK |
| `scope` | Human-readable scope (matches `sharing_scope`) |

---

*Next: [03 — EventStore, Projectors & Search](./03-eventstore-projectors-search.md)*
