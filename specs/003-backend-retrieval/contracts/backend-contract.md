# Knowledge Backend Contract Additions

**Intent**: Propose the narrow C003 additions C001 and C002 must reconcile before implementation.

## Ownership

C001 owns `knowledge/backend.py`; C002 owns the guarded mutation service. C003 may implement only accepted compatible additions. Host adapters never receive this raw mutation interface.

## Required Operations

```text
create_approved(value, operation_id) -> WriteResult
get(knowledge_id, version=None, include_retired=False) -> KnowledgeObject | NotFound
get_current_versions(knowledge_ids) -> mapping[knowledge_id, version]
search(query) -> RetrievalResponse
update_approved(knowledge_id, expected_version, value, operation_id) -> WriteResult | VersionConflict
set_relationships(relationships, expected_versions, operation_id) -> RelationshipWriteResult | VersionConflict
retire(knowledge_id, expected_version, operation_id) -> WriteResult | VersionConflict
delete(knowledge_id, expected_version, operation_id) -> DeleteResult | VersionConflict
rebuild_index() -> RebuildResult
health() -> BackendHealth
```

These reconciled signatures are canonical. C001 retains protocol ownership and C003 may add only compatible retrieval result types or implementation details.

## Command Rules

- Mutation commands are internal and already authorized by C002.
- Every semantic create, update, relationship, retire, and delete call receives the C002 `operation_id`.
- Retrying the same `operation_id` with identical semantic input returns the original result without another mutation; reuse with different semantic input fails.
- Update, relationship, retire, and delete calls carry all applicable expected versions.
- Commands contain approved domain values, not Basic Memory metadata keys.

## Result Rules

- Write results distinguish canonical durability from index readiness.
- Versioned reads and batch current-version lookup support C002 exact read-back and optimistic-version validation.
- Reads reconstruct host-neutral knowledge, provenance, and relations.
- Search always returns a bounded response and explicit retrieval/index status.
- Typed conflict, unavailable, partial-write/reconciliation, and index-degraded outcomes replace ambiguous booleans.
- No result implies approval, learner evidence, or host-work failure.

## Compatibility Conditions

- Do not remove or weaken any C001/C002 method or authorization invariant.
- Do not expose Basic Memory paths, private table identifiers, or unrestricted writes.
- Any sidecar proposal requires recorded C001 feasibility evidence and may contain no canonical content.
