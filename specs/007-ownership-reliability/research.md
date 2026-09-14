# Research: Ownership and Reliability

**Intent**: Record the minimum decisions needed to implement C007 without speculative infrastructure.

## Portable Representation

**Decision**: Export a directory or archive containing a versioned JSON manifest, JSONL records, and canonical Markdown files where supplied by the backend. Every listed file has a digest and record count.

**Rationale**: This form is inspectable, deterministic, streamable, and compatible with a file-oriented backend.

**Alternatives considered**: A custom binary bundle is opaque. A raw store copy couples restore to internal layouts and cannot validate record types safely.

## Restore Collision Policy

**Decision**: Validate and preflight all collisions before semantic writes. Missing records may be applied; records with the same identity, version, and digest are no-ops; any other identity/version collision rejects the restore. The MVP does not merge divergent repositories.

**Rationale**: This prevents silent overwrite without building another semantic merge path.

**Alternatives considered**: Last-write-wins violates optimistic concurrency. Interactive per-record merge duplicates the guarded revision workflow.

## Failure and Recovery State

**Decision**: Persist only content-free operation records containing `operation_id`, kind, object references, phase/status, and timestamps. `operation_id` is the sole idempotency identity. Index repair uses one content-free rebuild marker, not a content queue.

**Rationale**: This reconciles canonical-write/receipt gaps and rebuilds indexes from approved data without recovering candidates.

**Alternatives considered**: A durable job queue, event log, or distributed transaction coordinator is unnecessary for one local process and risks semantic payload persistence.

## Export and Restore Authorization

**Decision**: The actual user selection event creates one trusted, one-use bounded request. Export binds adapter/session/event, scope, and destination. Restore binds adapter/session/event, export ID, manifest digest, and fixed collision policy. Selection is authorization, so neither operation asks for redundant confirmation.

**Rationale**: The binding proves exact user intent while preserving a short ownership workflow. Model text and caller booleans remain outside the trusted event path.

**Alternatives considered**: An unbound method call can be forged. A second confirmation after an exact selection adds friction without strengthening the binding.

## Delete Completion

**Decision**: Execute a validated deletion plan idempotently across canonical content, indexes, approved excerpts, learning excerpts, relationships, and deferred references. Report each location and external limit; retain only disclosed content-free reference markers when required.

**Rationale**: Truthful resumable completion is safer than pretending heterogeneous stores form one atomic transaction.

**Alternatives considered**: Best-effort deletion without a report can falsely claim completion. Duplicating content in a side store violates the storage boundary.

## Search Degradation

**Decision**: Keep canonical durability and search health separate. On semantic-index failure, use C003's bounded local keyword path, return degraded status, and rebuild from canonical approved data.

**Rationale**: Recall stays local and index failure does not become a false write failure.

**Alternatives considered**: Remote embeddings violate local operation. A custom replacement index is unnecessary.

## Stored Content Boundary

**Decision**: Mark retrieval payloads as untrusted data in typed results. Authorization and control APIs accept trusted adapter events or guarded service objects, never retrieved strings. Use small deterministic secret minimization before proposal display.

**Rationale**: Structural separation is testable; prompt wording alone cannot enforce authorization.

**Alternatives considered**: A DLP engine or policy language exceeds the MVP.

## Local Transport

**Decision**: Validate the C001/C008-selected transport. Prefer a local socket; loopback is acceptable with supported local access restriction. Public bind addresses fail validation. Same-user privileged access remains outside the strong boundary.

**Rationale**: This uses host-supported mechanisms without adding IAM.

**Alternatives considered**: Production IAM does not protect against the OS owner and adds irrelevant infrastructure.

## Benchmark Method

**Decision**: Use a deterministic 10,000-object seed/corpus, warm-up phase, monotonic timings, raw samples, and a JSON result containing hardware, OS, Python, backend, index, corpus, command, and commit metadata.

**Rationale**: The targets require reproducible evidence, not telemetry infrastructure.

**Alternatives considered**: Remote monitoring and always-on metrics add no acceptance value.
