# 04 — Policy Engine

> Part of the [P2P Offline-First Memory](./README.md) design series.

---

## 1. Responsibilities

The Policy Engine is the **single decision authority** for all data movement in BrainCell. Nothing crosses a boundary (write, send, receive, store) without a policy evaluation.

| Decision | When evaluated |
|----------|---------------|
| `can_store(event, local_profile)` | On every write (local or received) |
| `can_send(event, peer_profile)` | Before including event in a sync batch |
| `can_receive(event, peer_profile)` | After receiving event from a peer (pre-store) |
| `admit_peer(peer_profile, local_profile)` | During handshake, before any sync |

---

## 2. Interface

```python
class PolicyEngine(Protocol):

    def admit_peer(
        self,
        peer: NodeProfile,
        local: NodeProfile,
    ) -> AdmissionResult:
        """
        Decide whether to establish a replication session with this peer.
        Returns AdmissionResult(allowed=True/False, reason=...).
        """
        ...

    def can_store(
        self,
        event: EventEnvelope,
        local: NodeProfile,
    ) -> PolicyDecision:
        ...

    def can_send(
        self,
        event: EventEnvelope,
        peer: NodeProfile,
    ) -> PolicyDecision:
        ...

    def can_receive(
        self,
        event: EventEnvelope,
        peer: NodeProfile,
    ) -> PolicyDecision:
        ...
```

```python
@dataclass
class PolicyDecision:
    allowed: bool
    reason: str   # human-readable; logged in audit trail

@dataclass
class AdmissionResult:
    allowed: bool
    reason: str
    session_max_classification: str | None = None
```

---

## 3. Evaluation Rules

Rules are evaluated in order. The **first matching deny wins**.

### 3.1 Residency Rules

```
IF policy.residency != "GLOBAL":
    DERIVE required_regions = expand_residency(policy.residency)
        # "EU"  → {AT, BE, BG, CY, CZ, DE, DK, EE, ES, FI, FR, GR, HR,
        #           HU, IE, IT, LT, LU, LV, MT, NL, PL, PT, RO, SE, SI, SK}
        # "US"  → {US}
        # "NL"  → {NL}
        # "GLOBAL" → all jurisdictions
    IF peer/local jurisdiction NOT IN required_regions:
        DENY  reason="residency violation: {policy.residency} required, got {jurisdiction}"
```

### 3.2 Legal Domain Rules

```
IF policy.legal_domain == "no-5eyes":
    IF peer/local derived_domains["5eyes"] == true:
        DENY  reason="legal domain: no-5eyes policy, peer is 5-eyes node"

IF policy.legal_domain == "eu-gdpr":
    IF peer/local derived_domains["EU"] == false:
        DENY  reason="legal domain: eu-gdpr policy, peer is non-EU node"
```

### 3.3 Sharing Scope Rules

```
IF policy.sharing_scope == "local-only":
    DENY for all non-local operations (can_send always false)
    ALLOW for can_store on local node

IF policy.sharing_scope == "org:<org_id>":
    IF peer.org_id != org_id:
        DENY  reason="scope violation: org mismatch"

IF policy.sharing_scope == "team:<team_id>":
    IF "team:<team_id>" NOT IN peer.groups:
        DENY  reason="scope violation: peer not in team"

IF policy.sharing_scope == "peer-group:<group_id>":
    IF "peer-group:<group_id>" NOT IN peer.groups:
        DENY  reason="scope violation: peer not in peer-group"
```

### 3.4 Classification vs Node Capability Rules

```
IF policy.classification == "restricted":
    IF NOT peer.capabilities.can_store_restricted:
        DENY  reason="node lacks capability to store restricted events"

IF classification_rank(policy.classification) > classification_rank(peer.capabilities.max_classification):
    DENY  reason="event classification exceeds node max_classification"
```

Classification rank: `public=0`, `internal=1`, `confidential=2`, `restricted=3`.

### 3.5 Transit Rules (Courier / Bundles)

```
IF peer.role == "courier" OR operation == "bundle_export":
    IF policy.may_transit == false:
        DENY  reason="policy.may_transit=false, event cannot be bundled/couriered"
    IF policy.classification IN ["confidential", "restricted"]:
        REQUIRE event.payload_cipher IS NOT NULL
        IF event.payload_cipher IS NULL:
            DENY  reason="courier transit requires encrypted payload for classification >= confidential"
```

### 3.6 Diode Rules

```
IF local.role == "diode-out":
    DENY all can_receive (this node only exports, never imports)

IF local.role == "diode-in":
    DENY all can_send (this node only imports, never exports)
```

### 3.7 Default: ALLOW

If no rule matched a DENY, the decision is **ALLOW**.

---

## 4. Jurisdiction & Region Mapping Config

Store as a YAML/JSON config file (`config/policy_regions.yaml`):

```yaml
regions:
  EU:
    - AT
    - BE
    - BG
    - CY
    - CZ
    - DE
    - DK
    - EE
    - ES
    - FI
    - FR
    - GR
    - HR
    - HU
    - IE
    - IT
    - LT
    - LU
    - LV
    - MT
    - NL
    - PL
    - PT
    - RO
    - SE
    - SI
    - SK

legal_domains:
  five_eyes:
    - US
    - GB
    - CA
    - AU
    - NZ
  nato:
    - AL
    - BE
    - BG
    - CA
    - CZ
    - DE
    - DK
    - EE
    - ES
    - FR
    - GR
    - HR
    - HU
    - IS
    - IT
    - LT
    - LU
    - LV
    - ME
    - MK
    - NL
    - NO
    - PL
    - PT
    - RO
    - SI
    - SK
    - TR
    - GB
    - US
```

---

## 5. Audit Logging

Every policy evaluation that results in a DENY **must** be logged.  
Every ALLOW at a boundary crossing (bundle export, bundle import, handshake) **should** be logged.

Log entry fields:

```json
{
  "ts": "2026-04-26T14:00:00Z",
  "decision": "DENY",
  "operation": "can_send",
  "event_id": "...",
  "event_type": "interactions.created",
  "peer_id": "...",
  "reason": "legal domain: no-5eyes policy, peer is 5-eyes node",
  "policy": { "...": "..." }
}
```

Use `structlog` (already a project dependency) and write to both the structured log stream and a dedicated audit log file (`logs/policy_audit.ndjson`).

---

## 6. Policy Defaults Per Cell

Cells expose a `default_policy()` method called when the actor does not explicitly provide a policy:

```python
class InteractionsCell(MemoryCell):

    def default_policy(self) -> Policy:
        return Policy(
            classification="internal",
            residency="EU",
            legal_domain="no-5eyes",
            sharing_scope=f"org:{settings.org_id}",
            retention_days=30,
            may_transit=True,
        )
```

---

## 7. Testing the Policy Engine

Unit-test each rule in isolation. Recommended test matrix:

| Test | Description |
|------|-------------|
| `test_residency_eu_allows_nl_node` | EU residency + NL node → ALLOW |
| `test_residency_eu_denies_us_node` | EU residency + US node → DENY |
| `test_no5eyes_denies_gb_node` | no-5eyes + GB node → DENY |
| `test_no5eyes_allows_nl_node` | no-5eyes + NL node → ALLOW |
| `test_local_only_denies_send` | local-only + can_send → DENY |
| `test_local_only_allows_store` | local-only + can_store on own node → ALLOW |
| `test_org_scope_denies_different_org` | org:itl + peer org:other → DENY |
| `test_restricted_denies_incapable_node` | restricted + node without can_store_restricted → DENY |
| `test_courier_transit_denied_without_encryption` | may_transit + confidential + plaintext → DENY |
| `test_diode_out_denies_receive` | diode-out role + can_receive → DENY |

---

*Next: [05 — Replication Protocol](./05-replication-protocol.md)*
