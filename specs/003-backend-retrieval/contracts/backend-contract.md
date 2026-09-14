# Knowledge Backend Contract Additions

**Intent**: Propose the narrow C003 additions C001 and C002 must reconcile before implementation.

## Ownership

C001 owns `knowledge/backend.py`; C002 owns the guarded mutation service. C003 may implement only accepted compatible additions. Host adapters never receive this raw mutation interface.

## Required Operations

```text
create_approved(command) -> WriteResult
get(id, version=None, include_retired=False) -> KnowledgeObject | NotFound
search(query) -> RetrievalResponse
update_approved(id, expected_version, command) -> WriteResult | VersionConflict
set_relationships(command) -> RelationshipWriteResult | VersionConflict
retire(id, expected_version, command) -> WriteResult | VersionConflict
delete(id, operation_key) -> DeleteResult
rebuild_index() -> RebuildResult
health() -> BackendHealth
```

Exact names may follow the C001 protocol. Semantic behavior must remain unchanged.

## Command Rules

- Mutation commands are internal and already authorized by C002.
- Every command carries its upstream operation/idempotency key.
- Update, relation, and retire commands carry all applicable expected versions.
- Commands contain approved domain values, not Basic Memory metadata keys.

## Result Rules

- Write results distinguish canonical durability from index readiness.
- Reads reconstruct host-neutral knowledge, provenance, and relations.
- Search always returns a bounded response and explicit retrieval/index status.
- Typed conflict, unavailable, partial-write/reconciliation, and index-degraded outcomes replace ambiguous booleans.
- No result implies approval, learner evidence, or host-work failure.

## Compatibility Conditions

- Do not remove or weaken any C001/C002 method or authorization invariant.
- Do not expose Basic Memory paths, private table identifiers, or unrestricted writes.
- Any sidecar proposal requires recorded C001 feasibility evidence and may contain no canonical content.
