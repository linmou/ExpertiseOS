# Contract: Guarded Consent and Knowledge Mutations

**Intent**: Freeze the host-neutral boundary consumed by backend, learning, host-adapter, reliability, and product-integration components.

## Proposal Boundary

The guarded service supports typed proposal creation for:

```text
propose_create(payload, origin, operation_id) -> PendingOperation
propose_revision(object_id, expected_version, payload, origin, operation_id) -> PendingOperation
propose_relation_change(change, expected_versions, origin, operation_id) -> PendingOperation
propose_retirement(object_id, expected_version, origin, operation_id) -> PendingOperation
decline(proposal_id, session_id, adapter_id) -> DeclineResult
expire_session(session_id) -> ExpiryResult
```

`origin` contains normalized adapter/session identity but is not itself authorization. Proposal payloads remain volatile.

## Grant Registration Boundary

Only a trusted host adapter path may call:

```text
register_user_decision(
  proposal_id,
  session_id,
  adapter_id,
  action,
  content_digest,
  user_event_ref,
  created_at,
) -> DecisionGrant
```

The caller must already have validated that `user_event_ref` identifies an actual host user-input event. Assistant/model/tool text and generic tool permission never enter this boundary as user events.

## Commit Boundary

```text
commit(proposal_id, grant_id, operation_id) -> CommitResult
```

The service performs, in order:

1. Load active proposal and unconsumed grant.
2. Validate proposal state, origin, action, digest, expected versions, operation validity, and exact match between submitted and proposal `operation_id`.
3. Call the matching explicit `KnowledgeBackend` semantic mutation with canonical `operation_id` and expected versions.
4. Read every committed record with versioned `get`, confirm its current version through `get_current_versions`, and compare every approved semantic field.
5. Insert or verify one exact approval receipt keyed by `operation_id`.
6. Consume the grant and mark the candidate approved.
7. Return `committed` only after all prior steps succeed.

## Backend Requirements from C001/C003

The narrow `KnowledgeBackend` contract supports these explicit methods; C002 does not add a generic mutation API:

```text
create_approved(value, operation_id) -> KnowledgeRecord
get(knowledge_id, version=None, include_retired=False) -> KnowledgeRecord | None
get_current_versions(knowledge_ids) -> Mapping[str, int]
search(query) -> tuple[SearchResult, ...]
update_approved(knowledge_id, expected_version, value, operation_id) -> KnowledgeRecord
set_relationships(relationships, expected_versions, operation_id) -> tuple[KnowledgeRecord, ...]
retire(knowledge_id, expected_version, operation_id) -> KnowledgeRecord
delete(knowledge_id, expected_version, operation_id) -> DeleteResult
```

Required behavior:

- The same `operation_id` and exact mutation returns the original `MutationResult` without another semantic mutation.
- Reusing an `operation_id` with different semantic input fails.
- Expected-version mismatch returns a typed conflict without mutation.
- Every semantic mutation receives its canonical `operation_id`.
- Mutation results identify every affected stable object ID/version for versioned `get` read-back and `get_current_versions` confirmation.
- The backend remains unreachable from host-facing mutation tools except through `KnowledgeService`.

`operation_id` is the final argument and sole idempotency identity for every semantic mutation. Search and version reads are non-mutating. Index rebuild is non-semantic maintenance and may use a separate content-free rebuild identifier if C003/C007 requires one.

For an approved grouped change, `KnowledgeService` calls these same explicit methods in the displayed effect order. Each call receives a deterministic child `operation_id` derived from the approved parent `operation_id` and the ordered effect identity. Replaying the parent reproduces the same child values, so already completed effects reconcile without a generic backend method or workflow engine.

Concrete Basic Memory mapping and retrieval are C003-owned.

## Result Semantics

`CommitResult` has one explicit status:

- `committed`: exact canonical result and receipt completed.
- `rejected`: approval or domain validation failed; no mutation attempted.
- `conflict`: expected versions were stale; no mutation occurred.
- `failed`: canonical mutation/read-back failed; no success receipt exists.
- `incomplete`: canonical mutation may have succeeded but receipt completion failed; retry only with the same proposal, grant, and `operation_id` while the interaction remains active.

No status other than `committed` may be presented as Saved.

## Exact Digest Document

The canonical document contains only displayed semantic fields relevant to the operation:

```text
operation_kind
content and shown knowledge metadata
approved source scope/provenance
relationship changes
expected object versions
grouped-operation effects when applicable
```

It excludes runtime-only proposal/grant IDs, `operation_id` values, generated timestamps, and unrelated prompts. Edit always recomputes the document and requires a matching decision.

## Downstream Extension Rules

- C003 may add approved read/search operations and backend mapping without adding a mutation bypass.
- C004 routes durable evidence/control changes through the same grant/digest/expected-version semantics and proposes SQLite migrations to C002 ownership.
- C005/C006 produce grants only from verified host user events and cannot weaken the core checks.
- C007 extends deletion/reliability behavior using the same `operation_id` contract and truthful result statuses.
- C008 exposes only guarded service operations at the host-facing tool/MCP boundary.
