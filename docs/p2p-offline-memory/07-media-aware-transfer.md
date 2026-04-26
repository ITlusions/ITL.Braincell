# 07 — Media-Aware Transfer

> Part of the [P2P Offline-First Memory](./README.md) design series.

---

## 1. Overview

Standard P2P replication assumes reliable, reasonably fast IP connectivity. In operational/field environments, BrainCell may need to transfer data over:

- **Low-bandwidth links** (satellite, 2G/3G, HF radio-over-IP)
- **High-latency links** (LEO/GEO satellite, long-haul serial)
- **Intermittent/store-and-forward links** (opportunistic WiFi, sneakernet USB)
- **Physical media** (USB drive, CD/DVD, SD card)

Media-aware transfer adapts the replication and bundle mechanisms to these constraints.

---

## 2. Payload Modes & Size Classes

### 2.1 Event Size Categories

| Category | Uncompressed size | Examples |
|----------|------------------|---------|
| `micro` | < 1 KB | simple tags, status flags |
| `small` | 1 KB – 64 KB | typical memory events (decisions, interactions) |
| `medium` | 64 KB – 1 MB | snippets with code, notes, structured reports |
| `large` | 1 MB – 50 MB | embedded documents, images, binary attachments |
| `bulk` | > 50 MB | log dumps, dataset snapshots |

### 2.2 Media Profile Configuration

```yaml
# config/media_profiles.yaml

profiles:
  default:
    max_event_size_bytes: 1048576    # 1 MB
    max_bundle_size_bytes: 104857600 # 100 MB
    compress: true
    compression_algorithm: zstd
    chunk_size_bytes: null           # no chunking

  low_bandwidth:
    max_event_size_bytes: 65536      # 64 KB
    max_bundle_size_bytes: 10485760  # 10 MB
    compress: true
    compression_algorithm: zstd
    chunk_size_bytes: 2097152        # 2 MB chunks
    bandwidth_limit_bytes_per_sec: 50000

  satellite:
    max_event_size_bytes: 8192       # 8 KB
    max_bundle_size_bytes: 2097152   # 2 MB
    compress: true
    compression_algorithm: zstd
    chunk_size_bytes: 524288         # 512 KB chunks
    bandwidth_limit_bytes_per_sec: 5000
    retry_delay_seconds: 30

  physical_media:
    max_event_size_bytes: 104857600
    max_bundle_size_bytes: 4294967296  # 4 GB (USB stick)
    compress: true
    compression_algorithm: zstd
    chunk_size_bytes: null
    checksum_algorithm: sha256
```

---

## 3. Chunked Bundle Transfer

When `chunk_size_bytes` is set, large bundles are split into numbered chunks.

### 3.1 Chunk File Structure

```
bundle-<bundle_id>-part001of010.bcchunk
bundle-<bundle_id>-part002of010.bcchunk
...
bundle-<bundle_id>-part010of010.bcchunk
bundle-<bundle_id>.manifest.json
bundle-<bundle_id>.manifest.sig
```

### 3.2 Chunk Manifest

```json
{
  "bundle_id": "<uuid>",
  "total_parts": 10,
  "chunks": [
    {
      "part": 1,
      "filename": "bundle-<uuid>-part001of010.bcchunk",
      "size_bytes": 2097152,
      "sha256": "<base64url>"
    },
    "..."
  ],
  "created_at": "2026-04-26T14:00:00Z",
  "source_node_id": "node-eu-prod-01"
}
```

### 3.3 Reassembly

The importer:
1. Collects all chunk files.
2. Verifies each chunk's `sha256` against the manifest.
3. Concatenates chunks in order to reconstruct the bundle.
4. Proceeds with standard bundle import (signature verification + event processing).

Missing chunks: log a warning with the missing part numbers. Do not proceed until all chunks are present.

---

## 4. Large Payload Handling

### 4.1 Inline vs. External Payloads

For events with `large` or `bulk` payload:

- **Inline**: Payload JSON/cipher is embedded directly in the EventEnvelope. Simple, works for ≤ 1 MB.
- **External**: Payload is stored as a separate blob file; EventEnvelope references it by content hash.

### 4.2 External Payload Reference

```python
@dataclass
class ExternalPayloadRef:
    storage_uri: str        # e.g. "local:data/blobs/<hash>" or "s3://..." 
    content_hash: str       # SHA-256 base64url of raw (pre-encryption) blob
    size_bytes: int
    mime_type: str
    encrypted: bool
    key_id: str | None
```

When `payload` contains `{"__external__": true, "ref": {...}}`, the replicator must:
1. Fetch the blob from `storage_uri` on the source.
2. Verify `content_hash`.
3. Store locally before confirming event receipt.

### 4.3 Blob Transfer API

```
GET /replication/blob/<content_hash>
```

Returns raw blob bytes (possibly encrypted). Only served to admitted peers with appropriate policy.

For low-bandwidth profiles, blob transfer can be deferred:
- Accept the event (reference only, blob missing).
- Mark blob as `pending_fetch`.
- Fetch blob when bandwidth is available.
- Search index marks event as `partial` until blob is present.

---

## 5. Bandwidth Throttling

```python
class ThrottledStream:
    def __init__(self, stream, bytes_per_sec: int):
        self._stream = stream
        self._bps = bytes_per_sec
        self._bucket = bytes_per_sec
        self._last_ts = time.monotonic()

    async def read(self, n: int) -> bytes:
        await self._wait_for_tokens(n)
        return await self._stream.read(n)

    async def _wait_for_tokens(self, n: int):
        while self._bucket < n:
            now = time.monotonic()
            elapsed = now - self._last_ts
            self._bucket = min(self._bps, self._bucket + elapsed * self._bps)
            self._last_ts = now
            if self._bucket < n:
                await asyncio.sleep(0.05)
```

Apply to both sync responses and bundle streaming.

---

## 6. Resume & Retry

For intermittent links:

- Sync cursors allow resuming from the last confirmed position.
- Chunked bundles track which chunks have been received (`chunks_received` in state file).
- Exponential backoff on transport errors with configurable max delay.

```yaml
retry:
  max_attempts: 10
  initial_delay_seconds: 5
  max_delay_seconds: 600
  backoff_factor: 2.0
```

---

## 7. Integrity Checks

All transfers include integrity checks regardless of media:

| Layer | Check |
|-------|-------|
| Chunk | SHA-256 per chunk (manifest) |
| Bundle | SHA-256 per event (event_hashes in manifest) |
| Event | Ed25519 signature (always) |
| Blob | SHA-256 of raw blob (external payload ref) |

If any check fails, the affected unit is rejected, logged, and quarantined. Other units continue processing.

---

*Next: [08 — Security, Crypto & Identity](./08-security-crypto-identity.md)*
