# Tasks: Approved Knowledge Retrieval Backend

**Input**: Design documents from `/specs/003-backend-retrieval/`
**Prerequisites**: C001 and C002 green promotion SHAs, `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: Required by the specification and constitution. Each new Python test begins with a Python shebang and a comment naming the responsible production file and behavior.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run independently in a different file after its stated prerequisites.
- **[Story]**: Maps work to the user story and its requirements.

## Phase 1: Setup and Upstream Gate

**Purpose**: Consume verified upstream contracts without guessing external APIs.

- [ ] T001 Merge the recorded C001 green integration SHA into `003-backend-retrieval` and verify pinned Basic Memory API/version evidence in `docs/compatibility.md` and `docs/basic-memory-license.md`
- [ ] T002 Merge the recorded C002 green integration SHA into `003-backend-retrieval` and inspect guarded mutation, domain, version, and idempotency contracts in `src/expertiseos/knowledge/service.py`, `src/expertiseos/knowledge/backend.py`, and `src/expertiseos/domain/models.py`
- [ ] T003 Reconcile proposed additions in `specs/003-backend-retrieval/contracts/backend-contract.md` with C001/C002 owners and record accepted signatures in `specs/003-backend-retrieval/contracts/backend-contract.md`
- [ ] T004 Verify the project test, type-check, and lint commands from `pyproject.toml` without adding a second toolchain

**Checkpoint**: Stop if C001 lacks supported public metadata/relation/history/delete/rebuild evidence or C002 lacks an authorized mutation/idempotency boundary.

---

## Phase 2: Foundational Host-Neutral Mapping

**Purpose**: Stabilize shared result and error values before story-specific adapter behavior.

- [ ] T005 Add only reconciled host-neutral retrieval/status values and compatible protocol signatures in `src/expertiseos/knowledge/backend.py` (FR-013, FR-019, FR-021)
- [ ] T006 [P] Add backend contract fixtures for approved objects, provenance, relationships, conflicts, filters, and health states in `tests/contract/test_knowledge_backend_contract.py` (FR-002-FR-004, FR-007-FR-013)
- [ ] T007 Implement explicit Basic Memory metadata mapping helpers for stable IDs, versions, lifecycle, semantic fields, operation keys, and source references in `src/expertiseos/backends/basic_memory.py` (FR-002, FR-003, FR-018, FR-021)
- [ ] T008 Implement typed canonical/index health and failure translation without private table access in `src/expertiseos/backends/basic_memory.py` (FR-013, FR-019, FR-021)
- [ ] T009 Run `pytest tests/contract/test_knowledge_backend_contract.py` and the C001/C002 focused suites; record exact command and result for the component report

**Checkpoint**: Host-neutral contract values compile and upstream behavior remains unchanged.

---

## Phase 3: User Story 1 - Recall Approved Knowledge with Context (Priority: P1)

**Goal**: Return bounded, filtered, approved active knowledge with provenance, relationships, conflicts, and untrusted-data labeling.

**Independent Test**: Seed approved/unapproved, active/retired, excluded, contradictory, and hostile records; assert exact filters, bounds, context, and no retrieval side effects.

### Tests

- [ ] T010 [P] [US1] Add bounded approved-only and scope/subject/category recall cases in `tests/integration/test_recall.py` (FR-006-FR-009; SC-002, SC-003)
- [ ] T011 [P] [US1] Add provenance availability and missing-source cases in `tests/integration/test_provenance.py` (FR-003, FR-007, FR-018; SC-001)
- [ ] T012 [P] [US1] Add relation/conflict coexistence and missing-target cases in `tests/integration/test_relationships.py` (FR-004, FR-007, FR-011; SC-001)
- [ ] T013 [US1] Add hostile recalled-content side-effect assertions in `tests/integration/test_recall.py` after T010 (FR-010; SC-009)

### Implementation

- [ ] T014 [US1] Implement approved/active filtering, scope exclusions, positive limit validation, and hard cap 20 in `src/expertiseos/backends/basic_memory.py` (FR-006, FR-008, FR-009)
- [ ] T015 [US1] Reconstruct source availability, relevant relationships, and distinct conflicts in `src/expertiseos/backends/basic_memory.py` (FR-004, FR-007, FR-011, FR-018)
- [ ] T016 [US1] Add the narrow bounded retrieval composition and untrusted-data labeling to `src/expertiseos/knowledge/service.py` without changing guarded mutation behavior (FR-006-FR-010, FR-021)
- [ ] T017 [US1] Run `pytest tests/integration/test_recall.py tests/integration/test_provenance.py tests/integration/test_relationships.py` and record exact results

**Checkpoint**: Ordinary recall exposes no unapproved, retired, deleted, or excluded record and has no grant/control/evidence side effect.

---

## Phase 4: User Story 2 - Preserve Exact Knowledge Across Storage (Priority: P1)

**Goal**: Round-trip approved objects, versions, provenance, and relationships through supported Basic Memory interfaces.

**Independent Test**: Authorized create/update/relation commands read back exactly; stale versions and duplicate deliveries cannot overwrite or duplicate state.

### Tests

- [ ] T018 [P] [US2] Add real-adapter exact create/read/version/status round-trip cases in `tests/integration/test_basic_memory_adapter.py` (FR-001-FR-003, FR-005; SC-001)
- [ ] T019 [US2] Add stale update and stable-ID version-history cases in `tests/integration/test_basic_memory_adapter.py` after T018 (FR-002, FR-005; SC-001)
- [ ] T020 [P] [US2] Add duplicate mutation and relationship delivery cases in `tests/integration/test_relationships.py` (FR-004, FR-020; SC-006)

### Implementation

- [ ] T021 [US2] Implement approved create, current/historical get, and exact semantic metadata/provenance mapping in `src/expertiseos/backends/basic_memory.py` (FR-001-FR-005, FR-018)
- [ ] T022 [US2] Implement expected-version update and stable-ID monotonic revision behavior in `src/expertiseos/backends/basic_memory.py` (FR-002, FR-019)
- [ ] T023 [US2] Implement idempotent approved relationship writes and reconstruction in `src/expertiseos/backends/basic_memory.py` (FR-004, FR-011, FR-020)
- [ ] T024 [US2] Run `pytest tests/integration/test_basic_memory_adapter.py tests/integration/test_provenance.py tests/integration/test_relationships.py` and record exact results

**Checkpoint**: Canonical approved knowledge round-trips exactly before downstream adapters consume it.

---

## Phase 5: User Story 3 - Continue Recall During Index Degradation (Priority: P2)

**Goal**: Provide honest local keyword fallback and separate canonical/index readiness.

**Independent Test**: Force local index initialization/query/update failure, block outbound network, and verify bounded filtered fallback over actual canonical records.

### Tests

- [ ] T025 [P] [US3] Add index initialization/query failure and bounded keyword cases in `tests/integration/test_keyword_fallback.py` (FR-006, FR-008, FR-012-FR-014; SC-003, SC-004)
- [ ] T026 [P] [US3] Add canonical-write-success/index-failure status cases in `tests/integration/test_index_failure_rebuild.py` (FR-013, FR-019; SC-010)
- [ ] T027 [US3] Add network-disabled direct-read and keyword-fallback smoke cases in `tests/integration/test_keyword_fallback.py` after T025 (FR-014; SC-007)

### Implementation

- [ ] T028 [US3] Implement local keyword matching over approved active canonical records with identical filters and cap in `src/expertiseos/backends/basic_memory.py` (FR-006, FR-008, FR-009, FR-012)
- [ ] T029 [US3] Implement indexed-to-keyword fallback and explicit mode/completeness/canonical/index status in `src/expertiseos/backends/basic_memory.py` (FR-012-FR-014, FR-019)
- [ ] T030 [US3] Surface retrieval degradation through `src/expertiseos/knowledge/service.py` without blocking unrelated host work or persisting queries (FR-012-FR-014, FR-019)
- [ ] T031 [US3] Run `pytest tests/integration/test_keyword_fallback.py tests/integration/test_index_failure_rebuild.py` including the network-disabled marker and record exact results

**Checkpoint**: Every forced index failure is visible and uses no remote fallback.

---

## Phase 6: User Story 4 - Retire, Delete, and Rebuild Safely (Priority: P2)

**Goal**: Make guarded lifecycle operations remove obsolete active recall/index traces while preserving permitted history and honest provenance.

**Independent Test**: Retire/delete actual approved fixtures, rebuild from canonical state, and prove ordinary recall and derived indexes contain no obsolete markers.

### Tests

- [ ] T032 [P] [US4] Add retire/current-versus-history and delete index-removal cases in `tests/integration/test_retire_delete_backend.py` (FR-005, FR-009, FR-015, FR-016; SC-005)
- [ ] T033 [P] [US4] Add idempotent rebuild, partial failure, and approved-canonical-only cases in `tests/integration/test_index_failure_rebuild.py` (FR-017, FR-019, FR-020; SC-005, SC-006)

### Implementation

- [ ] T034 [US4] Implement approved retirement and explicit retired-history reads in `src/expertiseos/backends/basic_memory.py` (FR-005, FR-015)
- [ ] T035 [US4] Implement idempotent backend-scope canonical/index deletion in `src/expertiseos/backends/basic_memory.py` and leave cross-store cleanup to C007 (FR-016, FR-020)
- [ ] T036 [US4] Implement idempotent index rebuild from active approved canonical objects only in `src/expertiseos/backends/basic_memory.py` (FR-017, FR-019, FR-020)
- [ ] T037 [US4] Run `pytest tests/integration/test_retire_delete_backend.py tests/integration/test_index_failure_rebuild.py` and record exact results

**Checkpoint**: Retired/deleted markers are absent from ordinary recall and active index state after rebuild.

---

## Phase 7: Cross-Cutting Verification and Handoff

- [ ] T038 Add the deterministic 10,000-object warm retrieval benchmark and environment metadata output in `tests/performance/test_retrieval_benchmark.py` (FR-006, FR-014; SC-008)
- [ ] T039 Run the complete component pytest suite plus the repository lint command and `mypy src/expertiseos`; record command, exit status, dependency versions, OS, hardware, corpus, and p95 evidence
- [ ] T040 Run the integration-owned real C002-authorized-write-to-C003-recall scenario in `tests/integration/test_authorized_write_to_recall.py` after serial integration (FR-001-FR-021; SC-001-SC-010)
- [ ] T041 Update C003 compatibility limits and verification evidence in integration-owned `docs/implementation-status.md` through the main integration owner
- [ ] T042 Review implementation against `specs/003-backend-retrieval/quickstart.md` and confirm no private-table access, remote fallback, custom ranking, query persistence, or unrestricted write surface was added

---

## Dependencies & Execution Order

- T001-T004 block all implementation. T001 and T002 must use recorded green integration SHAs.
- T005-T009 establish the reconciled contract and mapping foundation.
- US1 and US2 both depend on Phase 2; complete US2 before downstream producer-consumer promotion.
- US3 depends on canonical reads and US1 filtering. US4 depends on canonical mapping and retrieval filtering.
- T038-T042 run only after selected user stories are complete; T040 and T041 are integration-owner gates.

## Parallel Opportunities

- After T005, separate test files T010-T013 can be prepared in parallel.
- T018-T020, T025-T027, and T032-T033 are independent test-file tasks within their phases.
- Production work in `basic_memory.py` is serialized to one owner; `knowledge/backend.py` and `knowledge/service.py` changes require upstream reconciliation.

## Implementation Strategy

1. Land reconciled upstream contracts and foundation.
2. Complete US1 and US2 as the minimum backend/retrieval handoff.
3. Add US3 degradation behavior and US4 lifecycle/index behavior.
4. Run full static, integration, network-disabled, benchmark, and real producer-to-consumer gates.

Do not implement until orchestration planning reconciliation and dependency promotion pass.
