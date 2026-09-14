# Research: Consent Core

**Intent**: Resolve implementation choices that materially affect exact approval, concurrency, and interrupted-write correctness without adding speculative infrastructure.

## Typed Domain Representation

**Decision**: Use the single model approach established by C001, with explicit enums and flat records. If C001 selects dataclasses, every field has no definition-time default and callers supply all values.

**Rationale**: The domain is small, host-neutral, and validation-heavy. One representation avoids conversion drift at the approval digest boundary.

**Alternatives considered**: Mixing dataclasses and Pydantic was rejected because duplicate validation and serialization rules can change approval payloads. Subclass hierarchies per operation were rejected as unnecessary.

## Canonical Digest

**Decision**: Hash a typed semantic approval document encoded as canonical JSON using SHA-256. Sort keys and normalize unordered domain collections; retain exact content and semantically ordered displayed values.

**Rationale**: Standard structured serialization is deterministic, inspectable, and avoids ambiguous delimiter-based string concatenation. SHA-256 is locally available and sufficient for binding exact displayed data.

**Alternatives considered**: Hashing arbitrary object serialization was rejected because library/version details can drift. Ad hoc string joining was rejected because separators and optional fields can collide. Including timestamps/random proposal IDs was rejected because they are not semantic approval fields.

## One-Use Authorization

**Decision**: Store grants only in memory and consume them only after the canonical mutation, exact read-back, and receipt complete. The gate reserves no durable authorization state.

**Rationale**: This preserves retry within the active interaction while unused authorization disappears on restart. Consuming before durable success would force a redundant new approval after a transient failure.

**Alternatives considered**: Persisting unused grants was rejected by the privacy invariant. Consuming immediately after validation was rejected because it breaks bounded retry. Boolean approval parameters were rejected because callers could forge them.

## Idempotent Reconciliation

**Decision**: Pass a stable `operation_id` to each of C001's explicit backend mutation methods and require the same object/version result for repeats. Key receipts by the same `operation_id` and use insert-or-read-exact semantics. Do not add an operation journal or generic backend mutation method in C002.

**Rationale**: This directly handles the only partial ordering gap: canonical storage succeeded but receipt recording failed. A SQLite journal cannot be relied on during a SQLite failure, while `operation_id` replay on each narrow mutation prevents duplicate creates or revisions at their source.

**Alternatives considered**: A second generic backend mutation API, distributed transactions, two-phase commit, queues, and event sourcing were rejected as disproportionate. A content-free operation journal remains permitted only if implementation evidence exposes a recovery gap not covered by backend `operation_id` replay.

## Grouped Operation Replay

**Decision**: Represent an approved grouped change as an ordered list of existing explicit mutation calls. Derive each child `operation_id` deterministically from the approved parent `operation_id` and the child's ordered effect identity.

**Rationale**: The exact same child values are reproduced on retry, allowing completed effects to reconcile individually through C001's existing mutation methods.

**Alternatives considered**: A generic mutation endpoint or workflow engine was rejected because neither is needed to bind or replay a small approved group.

## Optimistic Concurrency

**Decision**: Bind all affected expected versions into the proposal digest and verify them at mutation time. Return a conflict and current version references rather than rebasing automatically.

**Rationale**: Cross-host changes remain predictable and cannot overwrite semantic disagreement silently.

**Alternatives considered**: Last-write-wins and distributed locks were rejected by the MVP. Automatic merge was rejected because it is itself a semantic change requiring user approval.

## Receipt Storage

**Decision**: Store one minimal `approval_receipts` table in SQLite with opaque IDs, affected object/version references as canonical JSON, digest, user-event reference, adapter ID, and UTC timestamp. Store no proposal payload or unrelated prompt.

**Rationale**: This is enough to inspect authorization provenance and reconcile retries while respecting the local minimal-state boundary.

**Alternatives considered**: Duplicating full approved knowledge in SQLite was rejected because canonical content belongs behind the knowledge backend. Separate tables per operation kind were rejected because they add no required behavior.

## Failure Semantics

**Decision**: Use typed domain failures for missing/invalid/expired approval, version conflict, backend failure, read-back mismatch, receipt failure, and incomplete reconciliation. The guarded mutation returns success only after all commit steps complete.

**Rationale**: Callers can continue ordinary work while reliably avoiding false Saved status or unsafe fallback writes.

**Alternatives considered**: Silent retry with changed content/configuration and generic success-with-warning were rejected because they weaken the approval contract.
