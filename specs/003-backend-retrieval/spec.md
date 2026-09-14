# Feature Specification: Approved Knowledge Retrieval Backend

**Feature Branch**: `003-backend-retrieval`
**Created**: 2026-09-14
**Status**: Draft
**Input**: User description: "Implement the MVP Basic Memory adapter and approved-only, bounded, provenance-aware retrieval without over-designing the product."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recall Approved Knowledge with Context (Priority: P1)

While working, a user can recall a small, relevant set of previously approved knowledge. Each result includes enough identity, version, condition, provenance, relationship, and conflict context to judge whether it applies, and stored text is treated as untrusted reference data.

**Why this priority**: Useful, safe recall is the main value this component provides and is required before either host integration can rely on saved knowledge.

**Independent Test**: Seed approved and unapproved records, search with a fixed query and limit, and verify that only the bounded approved set is returned with complete context and an explicit retrieval status.

**Acceptance Scenarios**:

1. **Given** approved knowledge that matches a query, **When** the user requests at most three results, **Then** no more than three approved results are returned with stable ID, version, content, categories, subjects, scope, evidential status, provenance availability, relationships, and known conflicts.
2. **Given** active, retired, and unapproved records, **When** ordinary recall runs, **Then** only active approved records within the requested scope are returned.
3. **Given** a matching record whose content contains instructions, **When** it is recalled, **Then** it remains labeled and handled as untrusted knowledge and cannot authorize writes, controls, or tools.
4. **Given** contradictory approved records, **When** either is recalled, **Then** both claims remain independently identifiable and the contradiction is exposed rather than silently resolved.

---

### User Story 2 - Preserve Exact Knowledge Across Storage (Priority: P1)

After an approved mutation has passed the consent service, users can read the same knowledge object by stable identity and version with its approved metadata, provenance, and relationships intact.

**Why this priority**: Retrieval cannot be trusted unless canonical approved objects round-trip exactly and concurrent semantic changes preserve stable identity and versions.

**Independent Test**: Send approved create, update, and relationship operations through the guarded upstream service boundary, then read each version by ID and compare every approved field and link.

**Acceptance Scenarios**:

1. **Given** an approved object, **When** it is stored and immediately read by stable ID, **Then** the returned object has the same content, metadata, provenance, status, and version.
2. **Given** an approved semantic revision with the current expected version, **When** it is stored, **Then** the stable ID is retained and the version increases monotonically.
3. **Given** a stale expected version, **When** an update is attempted, **Then** the existing object remains unchanged and a conflict is returned.
4. **Given** approved relationships with source information, **When** related objects are read, **Then** relationship type, endpoints, applicable versions, explanation, and provenance round-trip without exposing storage-specific details.

---

### User Story 3 - Continue Recall During Index Degradation (Priority: P2)

When local semantic indexing is unavailable, users can still search approved canonical knowledge through local keyword matching and can see that recall quality is degraded.

**Why this priority**: Retrieval failure must not block ordinary work or trigger a remote service, and users must not be misled about search completeness.

**Independent Test**: Disable semantic indexing in a fixed approved corpus, run the same query twice, and verify local keyword results, bounds, scope filtering, deterministic status, and no external network dependency.

**Acceptance Scenarios**:

1. **Given** an unavailable semantic index, **When** recall is requested, **Then** local keyword fallback searches only approved active knowledge and returns a visible degraded status.
2. **Given** no matching keyword result, **When** degraded recall completes, **Then** an empty bounded result with degraded status is returned without presenting the full repository.
3. **Given** a canonical approved write whose index update fails, **When** the object is read directly, **Then** the canonical object remains available and index readiness is reported separately.
4. **Given** outbound network access is blocked after setup, **When** direct reads and fallback searches run, **Then** local retrieval remains operational without an external memory or embedding call.

---

### User Story 4 - Retire, Delete, and Rebuild Safely (Priority: P2)

Users can retire or delete approved knowledge through the guarded mutation boundary, and retrieval reflects the resulting state without leaving active index entries or inventing missing provenance.

**Why this priority**: User ownership requires that recall and indexes honor retirement and deletion reliably.

**Independent Test**: Retire and delete approved fixtures through the guarded service, rebuild the index from canonical approved state, and verify direct reads, normal recall, links, and source availability.

**Acceptance Scenarios**:

1. **Given** a retired object, **When** ordinary recall runs, **Then** it is excluded while an explicit historical read can still resolve its stable identity and provenance.
2. **Given** an approved deletion, **When** recall and direct active reads run, **Then** deleted content and derived index entries are absent within the requested product scope.
3. **Given** an index containing obsolete entries, **When** rebuild completes, **Then** the index is recreated only from current approved canonical knowledge and produces no approval or learning event.
4. **Given** provenance whose source is no longer accessible, **When** the object is read, **Then** the original reference remains and is marked unavailable without fabricated replacement evidence.

### Edge Cases

- A requested limit is zero, negative, missing, or above the product maximum.
- Scope, subject, or category filters exclude every otherwise matching object.
- The same relationship is delivered twice or points to a missing, retired, or deleted target.
- A write times out after canonical persistence but before the caller sees success.
- An index update or rebuild fails partway while canonical approved data remains valid.
- Basic Memory is unavailable for direct reads, writes, or search.
- Provenance contains an approved excerpt but its external source later becomes unavailable.
- Search content contains hostile instructions, approval language, secrets, or control commands.
- Conflicting objects have different applicability scopes or evidential status.
- Concurrent revisions target the same stable object version.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST store and retrieve only mutations already authorized through the upstream guarded knowledge service; it MUST NOT expose an unrestricted host-facing persistence path.
- **FR-002**: The system MUST preserve stable knowledge IDs and positive, monotonically increasing versions across approved semantic revisions.
- **FR-003**: The system MUST round-trip approved content, categories, subjects, applicability scope, evidential status, active/retired status, contribution origin, source references, and timestamps without silently changing semantic meaning.
- **FR-004**: The system MUST round-trip approved relationships, including stable endpoints, optional endpoint versions, relation type, explanation, and source reference.
- **FR-005**: The system MUST provide direct reads by stable ID and optional version, including historical retired versions when explicitly requested.
- **FR-006**: The system MUST return a caller-specified bounded number of approved, active recall results and MUST enforce a product maximum for every query.
- **FR-007**: Recall results MUST include stable ID and version, approved semantic fields, provenance availability, relevant relationships, and known conflicts.
- **FR-008**: Recall MUST apply requested scope, subject, and category exclusions before results leave the retrieval boundary.
- **FR-009**: Ordinary recall MUST exclude unapproved, deleted, and retired content; it MUST NOT expose the complete knowledge repository by default.
- **FR-010**: Retrieved content MUST be explicitly represented as untrusted data and MUST NOT create an authorization, control change, tool permission, or learner evidence event.
- **FR-011**: Contradictory approved claims MUST remain distinct and retrieval MUST expose their conflict relation without automatic consolidation or overwrite.
- **FR-012**: If semantic indexing is unavailable, recall MUST use a local keyword fallback, preserve result bounds and exclusions, and return an explicit degraded-search status.
- **FR-013**: Search and direct reads MUST expose canonical-data and index readiness separately so an index failure does not hide a successful canonical approved write.
- **FR-014**: Retrieval and fallback MUST operate locally after setup and MUST NOT silently call a remote memory, embedding, or reranking service.
- **FR-015**: Approved retirement MUST exclude an object from ordinary recall while preserving explicitly requested history and resolvable lineage.
- **FR-016**: Approved deletion MUST remove in-scope canonical content and derived index entries so deleted content is not returned by active reads or recall.
- **FR-017**: Index rebuild MUST derive only from approved canonical knowledge and MUST NOT create approval, mutation, or learning events.
- **FR-018**: Missing source material MUST remain represented by its original source reference with an unavailable status; the system MUST NOT generate substitute provenance.
- **FR-019**: Backend and index failures MUST be surfaced accurately, MUST NOT report false mutation success, and MUST allow the host's unrelated work to continue.
- **FR-020**: Approved mutation retries MUST be idempotent so a timeout or duplicate delivery cannot create an extra object, version, relationship, or index event.
- **FR-021**: Storage-specific identifiers and metadata names MUST remain behind the backend contract; downstream callers consume host-neutral knowledge and retrieval results.

### Key Entities

- **Knowledge Object**: An approved, stable-ID record with versioned semantic content, classification, scope, evidential status, lifecycle status, contribution origin, and source references.
- **Source Reference**: Approved provenance identifying a source type and available host, session, event, artifact, excerpt, date, checksum, and accessibility details without hidden reasoning.
- **Relationship**: An approved typed semantic link between stable knowledge objects, optionally bound to endpoint versions and carrying an explanation and source reference.
- **Recall Query**: A non-durable query containing text, result limit, and optional subject, category, and scope hints or exclusions.
- **Recall Result**: A bounded view of an approved knowledge object with provenance availability, relevant relationships, known conflicts, and retrieval trust labeling.
- **Retrieval Status**: The observable state of canonical storage and indexing, including healthy, degraded keyword fallback, unavailable, and stale/rebuild-required conditions.
- **Backend Mapping**: The internal association that makes expertiseOS stable IDs, versions, and semantic fields recoverable through the supported local backend interface.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the approved-record fixture suite, 100% of direct create/read/update cases return exact approved content, stable identity, expected version, metadata, provenance, and relationships.
- **SC-002**: Across negative fixtures, 0 unapproved, deleted, retired, or scope-excluded records appear in ordinary recall.
- **SC-003**: Every recall request returns no more than its requested limit and no more than the configured product maximum, including degraded searches and empty-result cases.
- **SC-004**: In all simulated semantic-index failures, local keyword recall either returns bounded matching approved records or an empty result, and 100% of responses visibly report degradation.
- **SC-005**: After retirement, deletion, and index rebuild fixtures, 0 retired or deleted content markers appear in ordinary active recall or active derived indexes.
- **SC-006**: In timeout and duplicate-delivery fixtures, each approved operation produces exactly one canonical object/version and one set of relationships.
- **SC-007**: With outbound network access blocked after setup, 100% of direct-read and keyword-fallback scenarios complete without an external memory, embedding, or reranking request.
- **SC-008**: Warm local recall over 10,000 small approved objects completes in under one second at the 95th percentile on recorded test hardware.
- **SC-009**: In adversarial recalled-content fixtures, 0 stored instructions create a decision grant, state mutation, learner evidence event, or additional tool permission.
- **SC-010**: For every backend or index failure fixture, unrelated host work remains able to continue and no false successful mutation status is returned.

## Assumptions

- G0 supplies a tested local Basic Memory version, supported public interfaces, dependency constraints, and a narrow host-neutral backend contract.
- G1 supplies the guarded `KnowledgeService` mutation boundary, approval receipts, optimistic concurrency rules, domain objects, and approved-operation idempotency keys.
- The product maximum recall limit is a small configuration value fixed during implementation planning; callers may request a lower bound but cannot bypass it.
- Semantic search is optional for MVP operation; local keyword retrieval is the required fallback.
- Learner-state enrichment is owned by the learning component and may be joined downstream without changing canonical knowledge storage semantics.
- Export/restore orchestration and deletion of learner-evidence excerpts are owned by the reliability component; this component owns backend content/index effects and retrieval visibility.
- Host adapters, user interaction wording, behavioral prompts, service transport, and MCP exposure are outside this component.
- Cloud synchronization, a custom ranking model, remote embeddings/reranking, a graph database, and direct access to backend private tables are outside scope.
