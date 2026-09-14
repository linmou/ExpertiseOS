# Research: Approved Knowledge Retrieval Backend

**Intent**: Record the minimum technical decisions needed to implement the backend and retrieval component against upstream feasibility evidence.

## Basic Memory Integration

**Decision**: Use only the exact Basic Memory release and supported public interfaces verified by C001. Keep every package-specific name and representation inside `backends/basic_memory.py`.

**Rationale**: The MVP requires Basic Memory while forbidding coupling domain code to private storage details. C001 owns live capability and license evidence, so this component consumes that evidence rather than guessing an API.

**Alternatives considered**: Direct private-table access, replacing or forking Basic Memory, and a second canonical SQLite copy were rejected. A content-free stable-ID mapping is allowed only if C001 proves it necessary.

## Identity and Version Mapping

**Decision**: Treat upstream expertiseOS IDs as canonical and persist them, versions, lifecycle status, and operation keys as supported metadata. Backend paths and titles remain implementation details.

**Rationale**: Cross-host continuity, optimistic concurrency, lineage, deletion, and retry behavior require identity independent of display names or storage paths.

**Alternatives considered**: Content- or filename-derived identity and last-write-wins were rejected because edits would break identity or destroy concurrent semantic intent.

## Relationship Representation

**Decision**: Use the public relation/link mechanism C001 validates; otherwise encode the seven approved relation types in public metadata on canonical objects. Reconstruct host-neutral relationships on reads.

**Rationale**: This meets round-trip and conflict-retrieval needs without another database.

**Alternatives considered**: A graph database, general relationship repository, and silent relation inference were rejected.

## Search and Result Bound

**Decision**: Enforce a maximum of 20 results per call and require a positive caller limit. Apply active/approved and scope filters before results cross the service boundary.

**Rationale**: Twenty supports host comparison while preventing accidental full-vault return. Service and adapter both enforce the bound.

**Alternatives considered**: Unlimited search, a custom reranker, and a product-defined usefulness score were rejected.

## Degraded Retrieval

**Decision**: Prefer the supported local index when healthy. On initialization or query failure, run local keyword search against canonical approved data and return `degraded_keyword` plus separate canonical/index health.

**Rationale**: Local recall remains useful and honest without treating the index as canonical or adding remote services.

**Alternatives considered**: Remote fallback, silently empty healthy results, and a custom semantic engine were rejected.

## Query and Trust Boundary

**Decision**: Keep query text and intermediate ranking data in memory only. Mark every result as untrusted data and ensure retrieval has no mutation, grant, control, or learner-state side effect.

**Rationale**: Retrieval frequency and stored instructions must not acquire authority or become implicit evidence.

**Alternatives considered**: Query analytics and automatic mastery updates were rejected.

## Delete and Rebuild

**Decision**: Backend delete removes canonical content and derived index entries within its scope. Rebuild derives the index only from active approved canonical objects and is idempotent. C007 owns cross-store deletion policy.

**Rationale**: This preserves narrow component ownership while satisfying active-recall and index guarantees.

**Alternatives considered**: A background repair worker and durable content-bearing queue were rejected. C007 may own a content-free rebuild marker if needed.

## Performance Validation

**Decision**: Measure warm p95 retrieval using a deterministic corpus of 10,000 small approved objects and record environment metadata. Optimize only after correctness.

**Rationale**: This directly implements the MVP acceptance target without telemetry infrastructure.

**Alternatives considered**: Fake-only microbenchmarks and production telemetry were rejected.

## Upstream Evidence Required Before Implementation

- Exact Basic Memory version, supported OS scope, local-start procedure, and AGPL/release constraint.
- Public create/read/search/delete/rebuild and metadata/relation API evidence.
- Whether historical versions are supported directly and whether a content-free mapping is necessary.
- Existing C001 `KnowledgeBackend` signatures and C002 domain/result/error types.

No unresolved product clarification remains. Missing upstream evidence blocks adapter implementation rather than authorizing a silent alternative.
