# Feature Specification: Ownership and Reliability

**Intent**: Define the MVP behavior that keeps approved expertiseOS data portable, removable, recoverable, local, and safe under failure.

**Feature Branch**: `007-ownership-reliability`
**Created**: 2026-09-14
**Status**: Draft
**Input**: User description: "Implement the ownership, reliability, privacy, security-boundary, degraded-search, and performance requirements in the expertiseOS MVP agent plan without expanding the product architecture."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export and Restore Approved State (Priority: P1)

As the repository owner, I can export all approved expertiseOS-owned state in a documented portable form and restore it without losing stable identities, lineage, provenance, learning evidence, or control settings.

**Why this priority**: Data portability is the foundation of user ownership and a P0 completion requirement.

**Independent Test**: Populate approved knowledge, relationships, receipts, learning state, controls, and deferred references; export them; restore into an empty repository; and compare every supported record and reference while proving volatile proposal data is absent.

**Acceptance Scenarios**:

1. **Given** approved user-owned state, **When** the user exports it, **Then** the export contains the documented approved records and excludes unresolved candidates, unused grants, unrelated transcripts, and hidden reasoning.
2. **Given** a valid export and an empty destination, **When** the user authorizes restore, **Then** stable IDs, versions, lineage, relationships, provenance, evidence, settings, counters, and deferred references are restored consistently and search is rebuilt from approved canonical data.
3. **Given** a restore whose ID or version collides with local state, **When** validation runs, **Then** newer local data is not overwritten silently and the collision is reported before conflicting semantic state is changed.
4. **Given** foreign content rather than an expertiseOS export, **When** import is attempted, **Then** it remains outside approved knowledge until reviewed through the normal proposal and approval boundary.

---

### User Story 2 - Retire or Delete Owned Data (Priority: P1)

As the repository owner, I can retire knowledge while preserving history, or delete selected in-scope content from every expertiseOS-controlled persistent location with honest disclosure of what lies outside product control.

**Why this priority**: Retention choice and deletion integrity are mandatory privacy behavior.

**Independent Test**: Retire one approved object and delete another, then inspect canonical data, active recall, revisions, source excerpts, relationships, indexes, evidence excerpts, deferred activities, and disclosed markers.

**Acceptance Scenarios**:

1. **Given** an active approved object, **When** its exact retire operation is approved, **Then** its history and resolvable links remain while ordinary active recall excludes it.
2. **Given** an approved deletion scope, **When** deletion completes, **Then** in-scope canonical content, retained content-bearing revisions, index traces, approved excerpts, affected evidence excerpts, and invalid deferred activities are absent.
3. **Given** references to a deleted object, **When** deletion completes, **Then** they are removed or represented by a disclosed content-free unavailable marker according to the approved scope.
4. **Given** copies controlled by exports, backups, host providers, or external transcripts, **When** product deletion runs, **Then** the result identifies those limits and does not claim to have erased them.

---

### User Story 3 - Continue Safely Through Failures and Retries (Priority: P1)

As a user doing ordinary host work, I can continue that work when expertiseOS storage or search is unhealthy, while knowledge writes fail closed, completed canonical writes are not duplicated, and approved state can recover after restart.

**Why this priority**: False saves, duplicate semantic writes, or blocked host work would violate the core consent and reliability boundary.

**Independent Test**: Inject canonical-write, receipt-write, index-update, startup, and retry failures around one approved operation and prove the required status, durable records, idempotency, and recovery behavior at each boundary.

**Acceptance Scenarios**:

1. **Given** canonical storage is unavailable, **When** an approved mutation is attempted, **Then** no success receipt or false Saved result is produced and ordinary host work can continue.
2. **Given** canonical data and its approval receipt are complete but index update fails, **When** the operation returns, **Then** the save is reported as complete with degraded search status and only a bounded content-free repair marker remains.
3. **Given** canonical write success followed by receipt failure, **When** the same operation is retried, **Then** the existing canonical result is reconciled to one receipt without creating another object or version.
4. **Given** a process restart, **When** recovery runs, **Then** it loads approved durable state and content-free repair metadata only; it does not restore candidates, unused grants, or unapproved content.
5. **Given** repeated index rebuilds, **When** recovery completes, **Then** approved canonical data remains unchanged and no approval, evidence, or learning event is created.

---

### User Story 4 - Use a Local, Injection-Resistant Boundary (Priority: P1)

As the repository owner, I can rely on expertiseOS to treat recalled and tool-provided content as untrusted data, remain local after setup, and expose only an honest same-user security boundary.

**Why this priority**: Stored-content instructions must not become authorization, state changes, or data exfiltration paths.

**Independent Test**: Run malicious stored/file/tool fixtures and network-disabled local operations, then assert no grant, write, control change, extra tool permission, remote fallback, or unbounded disclosure occurs.

**Acceptance Scenarios**:

1. **Given** recalled or tool content instructing the system to approve, save, resume, mark mastery, invoke tools, or reveal the vault, **When** it crosses the service boundary, **Then** it is returned only as bounded untrusted data and causes none of those effects.
2. **Given** the local runtime has no outbound network after setup, **When** approved storage, state, recall, or search operations run, **Then** they use only local resources and no external embedding or memory endpoint is contacted.
3. **Given** the selected local transport, **When** the service starts with defaults, **Then** it does not listen publicly, uses local-user restrictions where supported, and accurately documents that same-user privileged processes are outside the strong boundary.
4. **Given** suspicious tokens or secrets in source content, **When** a proposal is formed, **Then** unnecessary values are omitted and any necessary excerpt remains explicitly scoped for approval.

---

### User Story 5 - Search and Uninstall Without Losing Control (Priority: P2)

As the repository owner, I receive useful local keyword results when semantic indexing is unavailable and can uninstall integrations while independently choosing whether to keep or delete my local data.

**Why this priority**: These complete the recovery and ownership experience after the core integrity behaviors are established.

**Independent Test**: Disable semantic indexing and verify visible bounded keyword results, then exercise both uninstall choices and inspect integration, service, repository, state, and deletion outcomes.

**Acceptance Scenarios**:

1. **Given** semantic indexing cannot initialize or fails, **When** the user searches, **Then** approved canonical knowledge remains available through bounded local keyword search with visible degraded status and no remote fallback.
2. **Given** uninstall is requested, **When** the user chooses to keep data, **Then** both host integrations and service registration are removed while local repository/state remain.
3. **Given** uninstall is requested, **When** the user chooses to delete data, **Then** integration and service registration are removed and the normal scoped deletion routine handles product-controlled data.

### Edge Cases

- An export is interrupted, malformed, from an unsupported schema version, or contains dangling references.
- Restore contains the same stable ID with an older, equal, or newer version than local state.
- Restore succeeds canonically but index rebuild fails; restored approved data remains authoritative and search reports degradation.
- Deletion is retried after partial index cleanup or encounters a missing source artifact.
- A relationship or deferred activity points to an object whose content is being deleted.
- A timeout occurs after a durable canonical mutation but before the caller receives acknowledgment.
- A stale repair marker refers to an already repaired or deleted object.
- Keyword fallback receives an empty query, a limit outside supported bounds, or a corpus with no match.
- A candidate marker appears in a host-owned transcript but nowhere under expertiseOS control.
- An embedding dependency needs an initial download; setup must make that step explicit rather than attempting it silently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST export approved knowledge objects and required versions, relationships, approved source references/excerpts, approval receipts, learner evidence, persisted learner summaries, controls, required aggregate progress, and deferred activities in a documented portable format.
- **FR-002**: The export MUST exclude unresolved candidates, unused decision grants, candidate queries, hidden reasoning, unrelated host transcripts, and all other unapproved content.
- **FR-003**: The system MUST validate export schema and version before restore and MUST reject malformed or unsupported input without partially changing semantic state.
- **FR-004**: Authorized restore MUST preserve stable identities, compatible lineage, provenance, relationships, approved learning state, controls, progress, and deferred references, then rebuild search from approved canonical data.
- **FR-005**: Restore MUST detect identity/version collisions and MUST NOT silently overwrite a newer local version.
- **FR-006**: Foreign semantic content MUST pass through the existing proposal and exact-approval boundary before entering the approved repository.
- **FR-007**: Retire MUST remain distinct from delete: retirement preserves content, lineage, provenance, and resolvable links while excluding the object from ordinary active recall.
- **FR-008**: Delete MUST remove approved in-scope content from canonical storage, derived indexes, retained content-bearing revisions, approved source excerpts, relevant learner-evidence excerpts, and deferred activities that can no longer remain valid.
- **FR-009**: Relationships affected by deletion MUST be removed or converted to disclosed content-free unavailable references according to the approved deletion scope.
- **FR-010**: Delete results MUST disclose limits for exported copies, operating-system backups, external host transcripts, provider retention, and forensic remnants outside product control.
- **FR-011**: Uninstall MUST remove both supported host integrations and stop/unregister the local service before applying an explicit keep-or-delete choice for local repository/state data.
- **FR-012**: Canonical write failure MUST produce no Saved result or success receipt and MUST leave ordinary host work able to continue.
- **FR-013**: Canonical write plus approval-receipt success with index failure MUST report the write as saved, expose degraded search, and persist at most bounded content-free repair metadata.
- **FR-014**: Approved mutations MUST use a stable operation/idempotency key so timeout retries, duplicate delivery, and receipt reconciliation create exactly one intended object/version and one corresponding receipt.
- **FR-015**: Startup recovery MUST load only approved durable state and content-free operation/repair markers; it MUST NOT restore unresolved candidates, reconstruct candidate text, replay unused grants, or perform automatic semantic consolidation.
- **FR-016**: Index rebuild MUST derive only from approved canonical data and MUST NOT create approval receipts, learner evidence, mastery changes, or reflection progress.
- **FR-017**: If semantic indexing is unavailable, search MUST use bounded local keyword retrieval, return a visible degraded status, preserve canonical knowledge availability, and MUST NOT call an external embedding service.
- **FR-018**: Retrieved, stored, file, and tool content MUST be treated as untrusted data and MUST NOT create decision grants, authorize writes or tools, change controls or mastery, or expand retrieval scope.
- **FR-019**: Proposal construction MUST minimize suspicious secrets/tokens and MUST require explicit approved scope before any necessary sensitive excerpt persists.
- **FR-020**: The local service MUST avoid public listening by default, apply local-user/session restrictions where supported, and disclose that unrestricted same-user or owner-level operating-system access is outside its strong security boundary.
- **FR-021**: After explicit setup dependencies are available, approved storage, state, and search operations MUST function without an outbound expertiseOS network dependency.
- **FR-022**: An automated persistence audit MUST inspect every expertiseOS-controlled persistent location and prove unique candidate markers are absent after Skip, ignore, cancel, and crash/restart cases while excluding host-owned transcripts from its scope.
- **FR-023**: Reliability and ownership operations MUST extend the approved-state, receipt, backend/index, and learner/control contracts through narrow interfaces without duplicating canonical knowledge in side stores or bypassing exact approval.
- **FR-024**: The system MUST measure lifecycle bookkeeping, warm local retrieval, and approved-write acknowledgment against the declared MVP targets using a deterministic 10,000-object corpus and record the test environment metadata.

### Key Entities

- **Portable Export**: A versioned manifest plus approved user-owned records and content, with enough identity and reference information for validation and restore.
- **Restore Report**: Validation and application outcome including schema compatibility, collisions, preserved records, rejected records, and index rebuild status.
- **Deletion Scope**: The exact objects, revisions, excerpts, evidence content, relationships, and dependent activities the user authorized to remove.
- **Deletion Result**: Removed product-controlled locations, retained disclosed content-free markers, unresolved external copies, and any recoverable failure status.
- **Operation Record**: A content-free identity and state for one approved mutation or repair, used only for idempotent reconciliation.
- **Search Health**: Search availability mode and repair need, distinct from canonical knowledge durability.
- **Uninstall Choice**: Explicit keep-or-delete selection for local repository/state after integration and service removal.
- **Persistence Audit Report**: Enumerated expertiseOS-controlled locations, marker checks, result, and fixture metadata without candidate content persistence.
- **Benchmark Result**: Latency distribution and environment/corpus metadata for one required operation class.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A round-trip export and restore reproduces 100% of supported approved records, stable IDs, required versions, lineage, relationships, provenance, evidence, settings, required progress, and valid deferred references in the deterministic fixture.
- **SC-002**: Across Skip, ignore, cancel, and crash/restart fixtures, the unique candidate marker is absent from 100% of enumerated expertiseOS-controlled persistent locations.
- **SC-003**: Retirement excludes the object from ordinary active recall while preserving 100% of its approved history and resolvable in-scope links.
- **SC-004**: Deletion removes the selected content from every enumerated expertiseOS-controlled in-scope location and reports every known out-of-product location limitation.
- **SC-005**: Timeout retry, duplicate delivery, and receipt-reconciliation fixtures each finish with exactly one intended object/version and one corresponding approval receipt.
- **SC-006**: Every canonical-write failure fixture produces zero false Saved results and zero success receipts while the surrounding host task remains able to proceed.
- **SC-007**: Every index-failure fixture preserves canonical approved data, reports degraded status, and permits successful repeatable rebuild without creating learning or approval events.
- **SC-008**: Every adversarial stored/file/tool fixture produces zero grants, writes, control/mastery changes, extra tool permissions, and out-of-scope retrieval effects.
- **SC-009**: With outbound networking blocked after setup, 100% of the deterministic local storage, state, keyword-search, and approved-write scenarios complete without an external expertiseOS call.
- **SC-010**: Lifecycle bookkeeping p95 is below 200 ms in the recorded benchmark environment.
- **SC-011**: Warm local retrieval p95 is below 1 second for 10,000 small approved knowledge objects in the recorded benchmark environment.
- **SC-012**: Approved-write acknowledgment p95 is below 1 second excluding indexing and host-model latency in the recorded benchmark environment.
- **SC-013**: Both uninstall choices remove all registered integrations and service startup entries; keep preserves local data and delete invokes the same verified scoped deletion behavior.

## Assumptions

- Upstream components provide the stable guarded mutation, approval receipt, canonical backend, index lifecycle, learner/control state, and deferred-reference contracts described by C002-C004.
- Selecting a valid expertiseOS export and confirming restore is explicit authorization for that restore operation; foreign content uses normal proposal approval.
- Portable representation uses documented human-inspectable files rather than a custom binary format.
- A content-free tombstone or repair marker is permitted only when required for referential integrity or recovery and is disclosed.
- Security claims cover the local product boundary, not hostile processes running with the same operating-system user or owner privileges.
- The benchmark is evidence for the declared test environment, not a universal hardware guarantee.

## Dependencies and Scope Boundaries

- **Upstream C002**: Supplies approved operation identity, exact approval, receipt lookup/write, and partial-write reconciliation semantics.
- **Upstream C003**: Supplies canonical approved-object enumeration/read/write, relationship handling, delete/index cleanup, index health/rebuild, and keyword retrieval capabilities.
- **Upstream C004**: Supplies learner evidence, summaries, controls, progress, and deferred-reference enumeration/restore/delete capabilities.
- **Downstream C008**: Owns shared service/MCP/skill wiring, host-facing orchestration, cross-host and complete acceptance scenarios.
- **Excluded**: Candidate recovery, host-specific adapter behavior, shared service/MCP wiring, cloud sync, telemetry, IAM/RBAC, DLP systems, distributed transactions, job queues, migration frameworks, and background workers.
