# Tasks: Ownership and Reliability

**Intent**: Provide an executable, dependency-ordered C007 implementation checklist with direct requirement and verification traceability.

**Input**: Design documents from `/specs/007-ownership-reliability/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: Focused negative-path, integration, static, network-disabled, and benchmark verification is required by the feature specification. This task list does not require the strict multi-agent TDD workflow.

**Python file header**: Every new Python source, test, or benchmark file MUST begin with a shebang followed by a comment naming the file responsibility and purpose. Dataclasses MUST declare every field without a default; defaults are supplied explicitly at construction sites.

## Phase 1: Setup and Contract Gate

**Purpose**: Confirm producer contracts and establish deterministic fixtures before feature work.

- [X] T001 Record the integrated C002-C004 promotion SHA and verify every required producer method in `specs/007-ownership-reliability/contracts/integration-handoffs.md`
- [X] T002 Validate the portable schema against supported and prohibited record types in `specs/007-ownership-reliability/contracts/export-manifest.schema.json`
- [X] T003 [P] Create deterministic approved-state, collision, malicious-content, and unique-marker fixtures with the required header in `tests/integration/fixtures/reliability_fixtures.py`
- [X] T004 [P] Define reusable fake approved-state/backend/learner producers with the required header in `tests/fakes_reliability.py`

**Checkpoint**: Implementation starts only when C002-C004 methods exist at the recorded green promotion SHA; contract mismatches return to their owners.

---

## Phase 2: Foundational Reliability and Boundary Types

**Purpose**: Establish content-free records, explicit statuses, and structural data boundaries used by every story.

- [X] T005 [P] Add model validation coverage for no-default dataclasses, export/restore request bindings, sole `operation_id` identity, prohibited semantic operation fields, search health, and bounded untrusted results with the required header in `tests/unit/test_ownership_models.py` (FR-013, FR-015, FR-018, FR-023, FR-025)
- [X] T006 [P] Add failure/retry/rebuild state-transition coverage with the required header in `tests/unit/test_reliability.py` (FR-012 through FR-017)
- [X] T007 [P] Add transport, untrusted-data, and sensitive-excerpt minimization coverage with the required header in `tests/unit/test_security_boundary.py` (FR-018 through FR-021)
- [X] T008 Implement no-default operation, restore, deletion, export, uninstall, and result dataclasses plus protocol types with the required header in `src/expertiseos/ownership.py` (FR-001 through FR-011, FR-023)
- [X] T009 Implement content-free operation state validation, explicit search health, reconciliation transitions, and bounded rebuild scheduling with the required header in `src/expertiseos/reliability.py` (FR-012 through FR-017)
- [X] T010 Implement untrusted result envelopes, public-bind rejection, and small deterministic secret minimization with the required header in `src/expertiseos/security.py` (FR-018 through FR-021)
- [X] T011 Run `mypy src/expertiseos/ownership.py src/expertiseos/reliability.py src/expertiseos/security.py` and `pytest tests/unit/test_ownership_models.py tests/unit/test_reliability.py tests/unit/test_security_boundary.py`, recording results in `artifacts/verification/c007-foundation.json`

**Checkpoint**: Every durable recovery record is proven content-free and retrieved data has no authorization/control path.

---

## Phase 3: User Story 1 - Export and Restore Approved State (Priority: P1)

**Goal**: Produce a portable approved-state bundle and restore it safely without silent collision merge.

**Independent Test**: Round-trip all supported records through actual C002-C004 snapshot/restore producers, then exercise malformed bundles and every collision class.

- [X] T012 [P] [US1] Add actual-user export/restore binding, replay/cross-session/altered-field rejection, no-redundant-confirmation, export allowlist, candidate/grant exclusion, manifest, and interrupted-write tests with the required header in `tests/integration/test_export_restore.py` (FR-001 through FR-004, FR-025, SC-001, SC-002)
- [ ] T013 [US1] Add actual producer round-trip, stable identity/reference, collision, foreign import, and index-rebuild-failure cases to `tests/integration/test_export_restore.py` (FR-004 through FR-006, SC-001, SC-007)
- [X] T014 [US1] Implement trusted export request binding validation, deterministic approved snapshot serialization, and atomic bound-destination publication in `src/expertiseos/ownership.py` (FR-001, FR-002, FR-025)
- [X] T015 [US1] Implement full-bundle schema/path/digest/count/reference validation and collision preflight in `src/expertiseos/ownership.py` (FR-003, FR-005)
- [X] T016 [US1] Implement trusted restore request binding validation, identical-record no-op, producer application ordering, and index-repair result in `src/expertiseos/ownership.py` (FR-004 through FR-006, FR-025)
- [X] T017 [US1] Run `pytest tests/integration/test_export_restore.py` and save record counts, IDs, digests, collision results, and index status in `artifacts/verification/c007-export-restore.json` (SC-001, SC-007)

**Checkpoint**: The supported approved record set round-trips exactly and every divergent collision stops before semantic mutation.

---

## Phase 4: User Story 2 - Retire or Delete Owned Data (Priority: P1)

**Goal**: Preserve retirement history and remove approved deletion scope from all product-controlled locations with honest reporting.

**Independent Test**: Retire one object and delete another through actual C002-C004 producers, inspect every controlled location, retry partial cleanup, and compare disclosed external limits.

- [X] T018 [P] [US2] Add retirement recall/history/link, scoped deletion, missing-source-unavailable, relationship, revision, excerpt, and invalid-deferred cases with the required header in `tests/integration/test_retire_delete.py` (FR-007 through FR-010, SC-003, SC-004)
- [X] T019 [P] [US2] Add keep/delete uninstall-choice contract cases with the required header in `tests/integration/test_uninstall_data_choice.py` (FR-011, SC-013)
- [X] T020 [US2] Implement exact approved retirement planning/result behavior against C002/C003 protocols in `src/expertiseos/ownership.py` (FR-007)
- [ ] T021 [US2] Implement enumerated idempotent deletion plans, actual C003/C004 cleanup, dependent-reference handling, and per-location results in `src/expertiseos/ownership.py` (FR-008, FR-009, FR-023)
- [X] T022 [US2] Implement explicit external deletion-limit reporting and keep/delete uninstall plans in `src/expertiseos/ownership.py` (FR-010, FR-011)
- [X] T023 [US2] Run `pytest tests/integration/test_retire_delete.py tests/integration/test_uninstall_data_choice.py` and record canonical/index/excerpt/evidence/deferred outcomes in `artifacts/verification/c007-delete-uninstall.json` (SC-003, SC-004, SC-013)

**Checkpoint**: Retirement remains resolvable; completed deletion has no selected content in any enumerated controlled location; uninstall never implies data deletion.

---

## Phase 5: User Story 3 - Continue Safely Through Failures and Retries (Priority: P1)

**Goal**: Keep host work available, prevent false success/duplicates, and recover approved state only.

**Independent Test**: Inject each canonical, receipt, index, timeout, duplicate-delivery, and restart boundary and count resulting objects, versions, receipts, evidence, and repair records.

- [X] T024 [P] [US3] Add canonical-outage, no-`committed`, and no-Saved-UI cases with the required header in `tests/integration/test_backend_outage.py` (FR-012, SC-006)
- [X] T025 [P] [US3] Add canonical-success/index-failure/repeatable-rebuild cases with the required header in `tests/integration/test_index_failure_rebuild.py` (FR-013, FR-016, SC-007)
- [X] T026 [P] [US3] Add timeout, duplicate delivery, and receipt-reconciliation cases proving `operation_id` is the sole identity with the required header in `tests/integration/test_idempotent_retry.py` (FR-014, SC-005)
- [X] T027 [P] [US3] Add restart recovery allowlist and prohibited candidate/grant/semantic-replay cases with the required header in `tests/integration/test_startup_recovery.py` (FR-015, SC-002)
- [X] T028 [US3] Implement canonical `committed`/receipt/index outcome classification and sole-`operation_id` reconciliation against actual C002/C003 protocols in `src/expertiseos/reliability.py` (FR-012 through FR-014)
- [X] T029 [US3] Implement approved-only startup recovery and repeatable canonical index rebuild in `src/expertiseos/reliability.py` (FR-015, FR-016)
- [X] T030 [US3] Run `pytest tests/integration/test_backend_outage.py tests/integration/test_index_failure_rebuild.py tests/integration/test_idempotent_retry.py tests/integration/test_startup_recovery.py` and record injected boundary plus object/version/receipt/evidence counts in `artifacts/verification/c007-recovery.json` (SC-005 through SC-007)

**Checkpoint**: Every write failure has an honest result, retries are single-effect, and restart never recovers unapproved semantic content.

---

## Phase 6: User Story 4 - Local Injection-Resistant Boundary (Priority: P1)

**Goal**: Keep stored/tool content inert, local transport private by default, and normal local operations network-independent.

**Independent Test**: Pass each malicious fixture through actual retrieval/service boundaries under outbound-network denial and verify zero authorization/control/tool side effects.

- [X] T031 [P] [US4] Add stored/file/tool instruction, bounded disclosure, and secret-minimization cases with the required header in `tests/integration/test_injection_boundary.py` (FR-018, FR-019, SC-008)
- [X] T032 [P] [US4] Add Skip/ignore/cancel/crash marker scans over actual C002-C004 controlled locations with the required header in `tests/integration/test_no_candidate_persistence_audit.py` (FR-022, SC-002)
- [X] T033 [P] [US4] Add outbound-network denial plus local storage/state/write/search cases with the required header in `tests/integration/test_no_network_runtime.py` (FR-020, FR-021, SC-009)
- [X] T034 [US4] Implement persistent-location enumeration and runtime marker audit with marker-free reports in `src/expertiseos/security.py` (FR-022)
- [X] T035 [US4] Integrate untrusted envelopes, minimization, and transport validation with actual C003 results and C008 handoff contracts in `src/expertiseos/security.py` (FR-018 through FR-021)
- [X] T036 [US4] Run `pytest tests/integration/test_injection_boundary.py tests/integration/test_no_candidate_persistence_audit.py tests/integration/test_no_network_runtime.py` and record location enumeration, side-effect counts, and blocked call attempts in `artifacts/verification/c007-security-local.json` (SC-002, SC-008, SC-009)

**Checkpoint**: Malicious data causes zero privileged effect and all local runtime paths pass with outbound expertiseOS networking denied.

---

## Phase 7: User Story 5 - Degraded Search and Uninstall Control (Priority: P2)

**Goal**: Return bounded keyword results during semantic failure and complete both explicit uninstall data choices.

**Independent Test**: Disable semantic indexing, verify actual C003 keyword output/status/bounds/no-network behavior, then repeat both uninstall choices through C008 integration.

- [X] T037 [P] [US5] Add empty-query, limit-bound, no-match, index-initialization, index-runtime-failure, and no-remote-fallback cases with the required header in `tests/integration/test_keyword_fallback.py` (FR-017, SC-007, SC-009)
- [X] T038 [US5] Implement explicit unavailable/semantic/keyword-degraded routing over C003 capabilities in `src/expertiseos/reliability.py` (FR-017)
- [X] T039 [US5] Run `pytest tests/integration/test_keyword_fallback.py tests/integration/test_uninstall_data_choice.py tests/integration/test_no_network_runtime.py` and record result bounds, health status, network attempts, and both uninstall outcomes in `artifacts/verification/c007-degradation-uninstall.json` (SC-007, SC-009, SC-013)

**Checkpoint**: Degradation is visible and local; uninstall keeps data unless deletion is explicitly chosen.

---

## Phase 8: Performance and Cross-Cutting Verification

**Purpose**: Produce reproducible performance, static, integration, and documentation evidence.

- [X] T040 [P] Create the deterministic corpus generator and percentile benchmark CLI with the required header, progress reporting, `--corpus-size`, `--seed`, and `--output` options in `benchmarks/benchmark_mvp.py` (FR-024, SC-010 through SC-012)
- [X] T041 Run `python benchmarks/benchmark_mvp.py --corpus-size 10000 --output artifacts/benchmarks/c007.json` and verify hardware, OS, Python, Basic Memory, index, corpus, command, commit, raw samples, and all p95 verdicts are present in `artifacts/benchmarks/c007.json` (SC-010 through SC-012)
- [X] T042 Run `mypy src/expertiseos/ownership.py src/expertiseos/reliability.py src/expertiseos/security.py benchmarks/benchmark_mvp.py` and save output/exit status in `artifacts/verification/c007-mypy.json`
- [X] T043 Run the complete C007 unit/integration suite and save command, exit status, test counts, durations, and environment versions in `artifacts/verification/c007-suite.json`
- [ ] T044 Run actual C002-to-C007, C003/C004-to-C007, and C007-to-C008 handoff tests listed in `specs/007-ownership-reliability/contracts/integration-handoffs.md` and save the tested integration SHA in `artifacts/verification/c007-handoffs.json` (FR-023, FR-025)
- [X] T045 Review `README.md`, `docs/privacy-boundary.md`, `docs/compatibility.md`, and `docs/implementation-status.md`, then record required owner changes and tested commit metadata without editing shared docs in `specs/007-ownership-reliability/implementation-handoff.md`

---

## Dependencies & Execution Order

- Phase 1 depends on green promoted C002-C004 contracts and blocks all implementation.
- Phase 2 depends on Phase 1 and blocks all user stories.
- US1, US2, US3, and US4 can proceed after Phase 2 against stable producer contracts; tasks sharing `ownership.py`, `reliability.py`, or `security.py` remain serial within each file.
- US5 depends on Phase 2 search health plus C003 keyword capability; its uninstall verification also depends on US2.
- Phase 8 depends on all selected user stories and the C008 consumer contract.

## Requirement Coverage

| Requirement group | Tasks |
|---|---|
| FR-001 to FR-006 / SC-001 | T012-T017 |
| FR-007 to FR-011 / SC-003, SC-004, SC-013 | T018-T023, T039 |
| FR-012 to FR-016 / SC-005 to SC-007 | T006, T024-T030 |
| FR-017 / keyword portions of SC-007 and SC-009 | T037-T039 |
| FR-018 to FR-022 / SC-002, SC-008, SC-009 | T007, T031-T036 |
| FR-023 / real handoffs | T001, T005-T010, T021, T028, T035, T044 |
| FR-024 / SC-010 to SC-012 | T040-T041 |
| FR-025 / trusted export-restore bindings | T005, T012, T014, T016, T044 |

## Implementation Strategy

Build Phase 2 first, then complete the smallest P0 slices in this order: failure/idempotency, export/restore, retire/delete, security/audit, degradation/uninstall. Keep contract mismatches with their upstream owners and integration wiring with C008. No compatibility layer or framework is planned.
