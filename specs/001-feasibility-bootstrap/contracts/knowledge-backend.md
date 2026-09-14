# KnowledgeBackend Contract

**Intent**: Freeze the minimum approved-data boundary needed by consent, retrieval, and reliability components.

## Responsibility

Store and retrieve canonical knowledge after authorization is enforced by the caller. Expose expertiseOS semantics while hiding Basic Memory payloads and internals.

## Interface

```python
class KnowledgeBackend(Protocol):
    def create_approved(
        self, value: ApprovedKnowledgeInput, operation_id: str
    ) -> KnowledgeRecord: ...
    def get(
        self,
        knowledge_id: str,
        version: int | None = None,
        include_retired: bool = False,
    ) -> KnowledgeRecord | None: ...
    def get_current_versions(
        self, knowledge_ids: tuple[str, ...]
    ) -> Mapping[str, int]: ...
    def search(self, query: SearchQuery) -> tuple[SearchResult, ...]: ...
    def update_approved(
        self,
        knowledge_id: str,
        expected_version: int,
        value: ApprovedKnowledgeInput,
        operation_id: str,
    ) -> KnowledgeRecord: ...
    def set_relationships(
        self,
        relationships: tuple[RelationshipInput, ...],
        expected_versions: Mapping[str, int],
        operation_id: str,
    ) -> tuple[KnowledgeRecord, ...]: ...
    def retire(
        self, knowledge_id: str, expected_version: int, operation_id: str
    ) -> KnowledgeRecord: ...
    def delete(
        self, knowledge_id: str, expected_version: int, operation_id: str
    ) -> DeleteResult: ...
    def rebuild_index(self) -> RebuildResult: ...
    def health(self) -> BackendHealth: ...
```

No approval boolean, unrestricted vendor write, cloud/team operation, or model call is exposed. `operation_id` is a runtime command argument and never a field of `ApprovedKnowledgeInput`, `RelationshipInput`, or stored semantic content.

## Invariants

- Only approved input reaches mutations.
- Every semantic mutation (create, update, relationship change, retire, and delete) receives `operation_id` as its sole idempotency identity.
- Stable IDs and monotonic versions survive round trips.
- `get(knowledge_id, version=None, include_retired=False)` returns the current active record by default, an exact retained version when requested, and retired records only when explicitly included.
- `get_current_versions(knowledge_ids)` returns the current version for each existing requested identity and supports atomic expected-version preparation without fetching semantic content.
- Updates, relation changes, and retirement reject stale versions.
- Search is bounded and reports match mode and index health.
- Canonical and index health are independent.
- Delete removes in-scope canonical and index entries.
- Repeating an `operation_id` with identical normalized command input returns its original result without another write. Reusing that `operation_id` with a different method, target, expected version, or semantic input returns a typed idempotency conflict.
- A new `operation_id` is a new command and remains subject to ordinary existence and expected-version rules.
- Delete requires an expected version. Index rebuild is non-semantic maintenance and is not part of the semantic mutation idempotency contract.
- Retrieved content remains untrusted data.
- Implementations avoid private Basic Memory tables.

## Fake Contract

The fake is process-local and deterministic, storing only explicitly approved test input. It supports configurable health, deterministic IDs, current and historical reads, version failures, delete/rebuild, exact command replay, and divergent-input conflict for a reused `operation_id`. It is not a production backend.

## Contract Checks

- Approved create/current-get/exact-historical-get round trip.
- Bounded search and fallback mode.
- Version conflicts for update/relation/retire.
- Delete/rebuild and health separation.
- Same-`operation_id`/same-input replay and same-`operation_id`/different-input conflict for every semantic mutation.
- Rejection of unapproved fake input.
