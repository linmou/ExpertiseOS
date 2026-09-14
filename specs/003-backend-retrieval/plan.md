# Implementation Plan: Approved Knowledge Retrieval Backend

**Branch**: `003-backend-retrieval` | **Date**: 2026-09-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-backend-retrieval/spec.md`

## Summary

Implement one thin Basic Memory adapter behind the G0 `KnowledgeBackend` protocol, plus retrieval-facing additions to the G1 `KnowledgeService`. Preserve expertiseOS stable IDs, versions, approved semantic metadata, provenance, and relationships through supported Basic Memory interfaces. Return bounded approved-only results with conflicts and trust labeling; when semantic indexing fails, use local keyword search and report degradation. Backend retirement, deletion, and index rebuild remain guarded operations initiated by the upstream consent service.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: G0-pinned Basic Memory release; Python standard library where practical; no remote embedding or reranking service  
**Storage**: Basic Memory canonical approved knowledge and local indexes; no duplicate canonical content in SQLite unless G0 evidence requires the smallest stable-ID sidecar  
**Testing**: pytest unit/contract tests, real Basic Memory integration tests, network-disabled smoke test, deterministic 10,000-object retrieval benchmark  
**Target Platform**: G0-supported local developer environments for Codex and Claude Code  
**Project Type**: One installable local Python package and one local service process  
**Performance Goals**: Warm local retrieval p95 below 1 second for 10,000 small approved objects on recorded hardware  
**Constraints**: Approved-only canonical data; maximum 20 recall results per request; keyword fallback; no private backend tables; no remote service; fail closed for writes and visibly degrade reads; no persistence of query text  
**Scale/Scope**: One user's local repository, 10,000-object acceptance corpus, seven relationship types, current and explicitly requested historical versions

## Constitution Check

*GATE: Passed before research and re-checked after design.*

| Principle | Design evidence | Status |
|---|---|---|
| Explicit Approval Before Persistence | Adapter mutation methods are internal consumers of G1 authorized commands; no host-facing raw backend access is introduced. | PASS |
| Work Continues, Unsafe Writes Stop | Canonical, index, and retrieval health are distinct; failures return typed status and never claim a failed write succeeded. | PASS |
| Local, Minimal, and Inspectable State | One adapter uses supported local Basic Memory interfaces; keyword fallback is local; no new service, queue, graph store, or custom ranking layer. | PASS |
| Permission, Knowledge, Evidence, and Mastery Stay Separate | Retrieval is read-only, untrusted data; it neither creates authorization nor changes learner state. | PASS |
| Contracts and Verification Drive Delivery | Backend/retrieval contracts, producer-consumer tests, real-backend integration tests, negative cases, and performance smoke evidence are explicit. | PASS |

Post-design re-check: PASS. The design adds no constitution exception and requires no complexity justification.

## Design Decisions

### Adapter boundary

- `BasicMemoryBackend` is the only module that knows Basic Memory metadata/path conventions.
- G0 owns the base `KnowledgeBackend` protocol. This component proposes only the narrow result/status and versioned-read additions recorded in [backend-contract.md](contracts/backend-contract.md).
- G1 owns the guarded mutation boundary. This component adds only retrieval composition to `KnowledgeService` and never bypasses its authorization checks.

### Stable identity and versions

- expertiseOS IDs are generated upstream and stored explicitly in supported Basic Memory metadata; Basic Memory paths or note titles are not public identity.
- Every canonical representation carries `expertiseos_id`, positive `version`, lifecycle status, and an idempotency/operation key for authorized mutation reconciliation.
- Historical version access uses supported backend history where G0 proves it adequate. If G0 proves it inadequate, a content-free mapping sidecar may locate canonical Basic Memory revisions; it must not duplicate knowledge content.

### Metadata, provenance, and relationships

- Store approved semantic fields explicitly and reconstruct host-neutral domain values on read.
- Store only approved source references/excerpts. Accessibility is mutable metadata; missing sources remain referenced as unavailable.
- Represent relationships through supported Basic Memory relation/link features or approved object metadata, whichever G0 validated. Do not inspect private tables or add a graph database.
- Preserve contradictory objects and `contradicts` links. Retrieval reports conflicts; it does not resolve them.

### Retrieval and degradation

- `KnowledgeService.search()` validates `1 <= limit <= 20`; absent public limits are normalized by the outer service, not the backend.
- The backend applies active/approved status and scope/subject/category exclusions before returning results, then enforces the limit again.
- Semantic/local indexed search is preferred only when healthy. A failure switches that request to supported local keyword search and returns `degraded_keyword` status.
- Query text and search scratch data remain volatile. Returned content is marked untrusted and carries no executable authority.
- Canonical health and index health are separate. A canonical write can succeed while search reports rebuild required.

### Retirement, deletion, and rebuild

- Retirement is a versioned semantic mutation from G1: retain history but exclude it from ordinary recall.
- Deletion removes the requested canonical content and derived index entries within backend scope. Reliability owns wider evidence/export cleanup.
- Rebuild discards/recreates derived index state only from current approved canonical objects. It is idempotent and emits no approval or learner event.

## Project Structure

### Documentation (this feature)

```text
specs/003-backend-retrieval/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── backend-contract.md
│   └── retrieval-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/expertiseos/
├── backends/
│   └── basic_memory.py
└── knowledge/
    ├── backend.py       # G0-owned; narrow compatible contract changes only
    └── service.py       # G1-owned; retrieval-facing changes only

tests/
├── contract/
│   └── test_knowledge_backend_contract.py
├── integration/
│   ├── test_basic_memory_adapter.py
│   ├── test_recall.py
│   ├── test_provenance.py
│   ├── test_relationships.py
│   ├── test_keyword_fallback.py
│   ├── test_retire_delete_backend.py
│   └── test_index_failure_rebuild.py
└── performance/
    └── test_retrieval_benchmark.py
```

**Structure Decision**: Use the repository's single-package layout. One adapter file contains all Basic Memory-specific translation. Tests are split only by existing verification layers; no repository, ranking, indexing, or relationship abstraction is added beyond the G0 backend protocol.

## Integration Dependencies

| Dependency | Required producer contract | Consumer impact |
|---|---|---|
| C001 feasibility/bootstrap | Pinned Basic Memory version, supported public create/read/search/delete/rebuild capabilities, `KnowledgeBackend`, backend test fake | Determines exact adapter calls and whether any content-free mapping is required. |
| C002 consent core | Domain objects, expected-version/idempotency semantics, guarded authorized mutation commands, `KnowledgeService` base | All mutations enter the adapter only after authorization; retrieval extends this service without changing approval behavior. |
| C004 learning controls | Learner-state lookup keyed by knowledge ID/version | Downstream integration may enrich recall results; this component does not store or infer learner state. |
| C005/C006 hosts | Bounded host-neutral recall request | Hosts receive only retrieval contract values and never Basic Memory internals. |
| C007 reliability | Wider deletion/export policy and failure recovery | This component supplies backend delete/rebuild primitives and status; reliability orchestrates cross-store effects. |
| C008 product integration | Service/MCP presentation and end-to-end scenarios | Integration verifies actual upstream authorized output flows into this adapter and real recall output flows downstream. |

## Verification Strategy

1. Contract tests run the same create/read/search/update/relation/retire/delete/rebuild behavior against the G0 fake and real adapter where supported.
2. Integration tests prove exact approved round trips, version conflicts, provenance/source availability, relation/conflict reconstruction, result bounds, filters, and absence of declined/unapproved markers.
3. Failure tests distinguish canonical failure from index failure, verify local keyword fallback, idempotent retry, and rebuild from approved canonical state only.
4. A network-disabled smoke test proves direct read and keyword fallback make no external memory/embedding call after setup.
5. The deterministic performance check records hardware, OS, Python, Basic Memory/index configuration, corpus size, and warm retrieval p95 for 10,000 small approved objects.
6. Integration promotion must run a real producer-to-consumer case: C002 authorizes and commits an object through C003, then `KnowledgeService.search()` returns that actual object without substituting a fake boundary.

## Complexity Tracking

No constitution violations or additional architecture layers are planned.
