# KnowledgeBackend Contract

**Intent**: Freeze the minimum approved-data boundary needed by consent, retrieval, and reliability components.

## Responsibility

Store and retrieve canonical knowledge after authorization is enforced by the caller. Expose expertiseOS semantics while hiding Basic Memory payloads and internals.

## Interface

```python
class KnowledgeBackend(Protocol):
    def create_approved(self, value: ApprovedKnowledgeInput) -> KnowledgeRecord: ...
    def get(self, knowledge_id: str, version: int | None) -> KnowledgeRecord | None: ...
    def search(self, query: SearchQuery) -> tuple[SearchResult, ...]: ...
    def update_approved(
        self, knowledge_id: str, expected_version: int, value: ApprovedKnowledgeInput
    ) -> KnowledgeRecord: ...
    def set_relationships(
        self,
        operation_id: str,
        relationships: tuple[RelationshipInput, ...],
        expected_versions: Mapping[str, int],
    ) -> tuple[KnowledgeRecord, ...]: ...
    def retire(self, knowledge_id: str, expected_version: int) -> KnowledgeRecord: ...
    def delete(self, knowledge_id: str) -> DeleteResult: ...
    def rebuild_index(self) -> RebuildResult: ...
    def health(self) -> BackendHealth: ...
```

No approval boolean, unrestricted vendor write, cloud/team operation, or model call is exposed.

## Invariants

- Only approved input reaches mutations.
- Stable IDs and monotonic versions survive round trips.
- Updates, relation changes, and retirement reject stale versions.
- Search is bounded and reports match mode and index health.
- Canonical and index health are independent.
- Delete removes in-scope canonical and index entries.
- Retried operation IDs are idempotent or typed conflicts.
- Retrieved content remains untrusted data.
- Implementations avoid private Basic Memory tables.

## Fake Contract

The fake is process-local and deterministic, storing only explicitly approved test input. It supports configurable health, deterministic IDs, version failures, delete/rebuild, and operation replay. It is not a production backend.

## Contract Checks

- Approved create/get round trip.
- Bounded search and fallback mode.
- Version conflicts for update/relation/retire.
- Delete/rebuild and health separation.
- Idempotent retry.
- Rejection of unapproved fake input.
