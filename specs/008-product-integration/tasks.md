# Tasks: Product Integration and Acceptance

**Intent**: Provide an executable, dependency-ordered task list that completes C008 without reopening upstream semantics or adding speculative infrastructure.

**Input**: Design documents from `/specs/008-product-integration/`
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and a recorded green integration promotion SHA containing C002-C007

**Tests**: Verification is required by the product specification. Use task-based implementation with focused contract, integration, end-to-end, static, and smoke checks; strict multi-agent TDD is not required.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other ready tasks because it owns a different file.
- **[Story]**: Maps the task to a user story in `spec.md`.
- Every task names its owned file and relevant requirement or acceptance coverage.

## Phase 1: Integration Gate and Setup

**Purpose**: Confirm dependencies and create only the assigned C008 paths.

- [X] T001 Record and verify the immutable green C002-C007 promotion SHA against the Dependency Gate in `specs/008-product-integration/plan.md`
- [X] T002 Inspect the promoted public contracts for consent, retrieval, learning/controls, both hosts, and ownership/reliability and record any mismatch in `specs/008-product-integration/research.md`
- [X] T003 Verify C004 exposes pass-only mastery advancement with inspectable non-pass outcomes and unchanged autonomous safeguards in `specs/008-product-integration/research.md` (FR-019)
- [X] T004 Create the assigned module and test path skeleton only where absent: `skill/SKILL.md`, `src/expertiseos/service.py`, `src/expertiseos/mcp_server.py`, `tests/e2e/`, and `examples/reference_scenarios/`
- [X] T005 Validate imported C001 project commands and pinned dependency/host versions without changing configuration, and record the commands used in `specs/008-product-integration/quickstart.md`

**Checkpoint**: C008 may proceed only when the promoted interfaces match the reconciled contracts. Contract drift returns to the integration owner.

---

## Phase 2: Foundational Test and Fixture Support

**Purpose**: Establish shared component-local helpers without reimplementing upstream domain behavior.

- [X] T006 Implement fixtures that construct the real promoted service graph and normalized host clients in `tests/e2e/conftest.py` (FR-009, SC-010)
- [X] T007 [P] Implement a safe acceptance-evidence builder that records `tested_sha` without requiring a future promotion SHA, matching `contracts/acceptance-evidence.md`, in `tests/e2e/evidence.py` (FR-010, FR-011)
- [X] T008 [P] Implement assertions for approved-store deltas, volatile-state expiry, and marker absence without persisting candidate content in `tests/e2e/assertions.py` (FR-009, SC-001)
- [X] T009 Add a test that fails when an E2E boundary replaces a required promoted producer with a synthetic substitute in `tests/e2e/test_handoff_integrity.py` (FR-009, SC-010)
- [X] T010 Run the foundational E2E support checks and record command, exit code, tested SHA, and output path through `tests/e2e/evidence.py`; leave later promotion mapping to integration review

**Checkpoint**: Tests can consume actual promoted upstream artifacts and emit safe, complete evidence.

---

## Phase 3: User Story 1 - One Guarded Product Surface (Priority: P1)

**Goal**: Expose the minimum host-neutral operations without a persistence bypass.

**Independent Test**: Exercise every registered operation through a host-neutral client and prove reads are bounded, exact authorized commits succeed once, and unauthorized/model-authored mutation attempts create no persistent delta.

### Verification

- [X] T011 [P] [US1] Add composition-facade contract cases for read `ok` and mutation `committed`, `rejected`, `conflict`, `failed`, `incomplete`, `degraded`, and `unavailable` results in `tests/e2e/test_service_surface.py` (FR-001, FR-003, FR-006)
- [X] T012 [P] [US1] Add MCP registry allowlist, forbidden backend/boolean-approval exposure checks, trusted user-event-bound export/restore selection cases, and guarded deferred-removal cases in `tests/e2e/test_mcp_surface.py`, including rejection of activity-reference-only removal and model/caller authorization assertions (FR-001, FR-002)
- [X] T013 [US1] Add actual guarded commit tests covering exact decision binding, one-use behavior, stale version, changed digest, cross-session grant, and retry using canonical `operation_id` as the sole idempotency identity in `tests/e2e/test_acceptance_consent.py` (AT-04, AT-05, AT-06, AT-07, AT-08)

### Implementation

- [X] T014 [US1] Implement the stateless dependency-composition facade with canonical mutation `operation_id` handling and precise read/mutation `ToolResult` mapping in `src/expertiseos/service.py` (FR-001, FR-003, FR-006)
- [ ] T015 [US1] Implement the explicit MCP read, proposal, guarded commit, learning/control, ownership, capability, and health registrations in `src/expertiseos/mcp_server.py` (FR-001, FR-002) - integration-blocked pending the C002 Decimal canonicalization correction receipt required by typed `ControlSettings`
- [X] T016 [US1] Ensure `src/expertiseos/mcp_server.py` exposes no backend writer, generic execute operation, direct mastery setter, caller-supplied approval assertion, or mutation idempotency identity other than `operation_id` (FR-002)
- [X] T017 [US1] Run `tests/e2e/test_service_surface.py`, `tests/e2e/test_mcp_surface.py`, and `tests/e2e/test_acceptance_consent.py`; prove Saved derives only from `committed`, then record evidence and inspect the persistent-state delta (SC-001)

**Checkpoint**: The host-neutral surface is useful for reads and guarded workflows, but structurally cannot bypass promoted approval semantics.

---

## Phase 4: User Story 2 - Consistent Learning Behavior (Priority: P1)

**Goal**: Give both hosts one restrained behavior source for recall, proposals, reflection, and controls.

**Independent Test**: Apply the shared behavior fixtures to both promoted adapter contracts and compare observable behavior for their common declared capabilities.

### Verification

- [X] T018 [P] [US2] Add shared-skill structural checks for one canonical behavior source and no duplicated host policy in `tests/e2e/test_shared_skill.py` (FR-004)
- [X] T019 [P] [US2] Add adversarial retrieved/tool content fixtures to `examples/reference_scenarios/adversarial_content.json` (FR-005, AT-15)
- [X] T020 [US2] Add behavior cases for bounded search, uncertainty-safe wording, eligible checkpoints, save-without-learning, one-step optional reflection, and upstream control decisions in `tests/e2e/test_shared_skill.py` (AT-02, AT-03, AT-07, AT-10, AT-11)
- [X] T021 [US2] Add pass-only mastery advancement and inspectable `partial`/`fail`/`insufficient_evidence` cases, including autonomous safeguards under threshold configuration, in `tests/e2e/test_acceptance_learning_controls.py` (AT-09, FR-019)
- [X] T022 [US2] Add adversarial assertions for zero grants, writes, control changes, mastery changes, vault-wide disclosures, and extra permissions in `tests/e2e/test_acceptance_reliability.py` (AT-15, SC-006)

### Implementation

- [X] T023 [US2] Implement the single host-neutral search, compare, novelty-language, proposal, optional reflection, recall, and control behavior specification in `skill/SKILL.md` (FR-004)
- [X] T024 [US2] Define in `skill/SKILL.md` that retrieved and tool-provided content is untrusted data and cannot authorize tools, writes, control/mastery changes, or disclosure (FR-005)
- [X] T025 [US2] Define in `skill/SKILL.md` that the promoted service is authoritative for state and errors, ordinary host work continues on failure, and host capability limits are reported accurately (FR-006)
- [X] T026 [US2] Run shared-skill, learning/control, and adversarial checks against both adapter contracts and record differences only where capabilities declare them (SC-002, SC-006)

**Checkpoint**: Codex and Claude Code consume one behavior contract, and model instructions cannot substitute for service authorization.

---

## Phase 5: User Story 3 - Cross-Host Safety (Priority: P1)

**Goal**: Prove shared durable state and isolated volatile authorization across hosts.

**Independent Test**: Save in one host, retrieve in the other, race versioned edits, attempt approval reuse, and inspect global reflection counting.

### Verification and Integration

- [X] T027 [P] [US3] Add the cross-host continuity fixture with stable identity, provenance, relations, uncertainty, learner state, and controls to `examples/reference_scenarios/cross_host.json` (Scenario D, AT-12)
- [X] T028 [US3] Add Codex-to-Claude and Claude-to-Codex approved-state continuity cases in `tests/e2e/test_acceptance_cross_host.py` (FR-007, AT-12)
- [X] T029 [US3] Add cross-host and cross-session decision-grant reuse rejection cases in `tests/e2e/test_acceptance_cross_host.py` (AT-06, AT-12)
- [X] T030 [US3] Add the version-3 concurrent edit fixture where the second approved commit conflicts with version 4 in `tests/e2e/test_acceptance_cross_host.py` (AT-12)
- [X] T031 [US3] Add one-global-reflection-count and no-host-switch-mastery cases in `tests/e2e/test_acceptance_cross_host.py` (AT-09, AT-12)
- [X] T032 [US3] Run the complete cross-host suite against the actual shared promoted service and record the matching IDs, versions, content, provenance, relations, learner state, controls, counts, and zero approval reuse (SC-005)

**Checkpoint**: Durable state is common, volatile authorization is isolated, and stale writes cannot overwrite.

---

## Phase 6: User Story 4 - Reference Journeys (Priority: P2)

**Goal**: Make the four PRD journeys concise, executable, and inspectable.

**Independent Test**: Run each fixture from its declared initial state and compare visible outputs, persistent deltas, and final volatile state exactly.

### Fixtures

- [X] T033 [P] [US4] Add Scenario A new-observation, save-now, reflect-later fixture to `examples/reference_scenarios/new_observation.json` (AT-04, AT-07, AT-08)
- [X] T034 [P] [US4] Add Scenario B conflict-without-silent-replacement fixture to `examples/reference_scenarios/conflict.json` (AT-02, AT-08)
- [X] T035 [P] [US4] Add Scenario C fatigue-before-target fixture to `examples/reference_scenarios/fatigue.json` (AT-10, AT-11)
- [X] T036 [US4] Validate all four fixtures against the `ReferenceScenario` rules in `specs/008-product-integration/data-model.md` using `tests/e2e/test_reference_scenarios.py` (FR-008)

### Scenario Execution

- [X] T037 [US4] Implement Scenario A execution and exact approved/volatile delta assertions in `tests/e2e/test_reference_scenarios.py`
- [X] T038 [US4] Implement Scenario B execution and coexistence/revision/decline assertions in `tests/e2e/test_reference_scenarios.py`
- [X] T039 [US4] Implement Scenario C execution and fatigue/target/recall assertions in `tests/e2e/test_reference_scenarios.py`
- [X] T040 [US4] Implement Scenario D execution and cross-host continuity/isolation assertions in `tests/e2e/test_reference_scenarios.py`
- [X] T041 [US4] Run Scenario A-D from clean declared states and record exact visible outputs, persistent deltas, volatile end states, and edge artifacts (SC-003)

**Checkpoint**: All four user journeys pass through real promoted services with no hidden fixture implementation of domain behavior.

---

## Phase 7: User Story 5 - Deterministic Acceptance Verdict Input (Priority: P2)

**Goal**: Produce complete component-local evidence for AT-01 through AT-16 while keeping final verdict ownership with integration.

**Independent Test**: Run every applicable case with complete evidence metadata and prove that deterministic P0 failures cannot be offset by model-behavior observations.

### Acceptance Coverage

- [X] T042 [P] [US5] Add AT-01 to AT-03 activation, scope-exclusion, novelty/conflict, and atomic-checkpoint cases in `tests/e2e/test_acceptance_hosts.py` (FR-012, FR-013)
- [ ] T043 [US5] Complete and map AT-04 through AT-08 cases in `tests/e2e/test_acceptance_consent.py` (FR-014)
- [ ] T044 [US5] Complete and map AT-09 through AT-11 cases in `tests/e2e/test_acceptance_learning_controls.py` (FR-015)
- [ ] T045 [US5] Complete and map AT-12 cases in `tests/e2e/test_acceptance_cross_host.py` (FR-015)
- [ ] T046 [US5] Add AT-13 through AT-16 outage, index failure, export/restore/delete, adversarial, and offline cases in `tests/e2e/test_acceptance_reliability.py` (FR-016)
- [X] T047 [US5] Add fixture-corpus coverage for six categories, three subjects, duplicate, changed condition, contradiction, uncertain novelty, unavailable source, malicious content, and a non-coding task in `examples/reference_scenarios/acceptance_corpus.json` (SC-009)
- [ ] T048 [US5] Add an offline boundary fixture that blocks expertiseOS runtime network access while separating host inference in `tests/e2e/test_acceptance_reliability.py` (AT-16, SC-007)

### Evidence and Gates

- [X] T049 [US5] Add a completeness test requiring exactly AT-01 through AT-16 mappings and all acceptance-evidence fields in `tests/e2e/test_acceptance_manifest.py` (FR-009, FR-011)
- [X] T050 [US5] Add a verdict-input test where any applicable consent, privacy, or state-integrity failure blocks promotion regardless of model-behavior scores in `tests/e2e/test_acceptance_manifest.py` (FR-017)
- [ ] T051 [US5] Run all deterministic automated AT cases at the immutable tested SHA and persist safe component evidence through `tests/e2e/evidence.py` (SC-004)
- [ ] T052 [US5] Run pinned live Codex and Claude Code cases supported by C001/C005/C006, recording exact versions, capability limits, commands, input fixtures, outputs, and exit codes through `tests/e2e/evidence.py` (SC-004)
- [ ] T053 [US5] Run the offline expertiseOS and keyword-fallback scenario with outbound access blocked and record network-mode evidence through `tests/e2e/evidence.py` (SC-007)
- [ ] T054 [US5] Run model-behavior fixtures separately and record misses/false proposals without changing deterministic results in `tests/e2e/evidence.py` (FR-010)

**Checkpoint**: C008 supplies complete reproducible evidence; the integration owner decides and records the authoritative final acceptance verdict.

---

## Phase 8: Full Verification and Owner Handoff

**Purpose**: Close the component with integration-ready evidence and no shared-file overreach.

- [ ] T055 Run the full targeted `tests/e2e/` suite and record zero unexpected skips for required deterministic cases
- [ ] T056 Run the full repository test suite against the promoted upstream components and route component-local regressions to their stable owners
- [ ] T057 Run repository lint, formatting, and static/type checks, including mypy for modified Python modules
- [ ] T058 Run the repository smoke/install command and verify both host packages reference the same `skill/SKILL.md`
- [ ] T059 Inspect the final diff to confirm changes are limited to C008-owned source paths and `specs/008-product-integration/`
- [ ] T060 Provide the integration owner with the component commit SHA, commands, exit codes, evidence paths, capability limits, upstream defects found, and files intentionally not added

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 requires a green integration promotion containing C002-C007.
- Phase 2 depends on Phase 1 and blocks all user-story work.
- Phases 3 and 4 both depend on Phase 2; implement Phase 3 before Phase 4 when one owner is working because the skill calls the tool surface.
- Phase 5 depends on Phase 3 and the promoted adapters; its tests may reuse Phase 4 behavior fixtures.
- Phase 6 depends on Phases 3-5.
- Phase 7 depends on all product stories and the promoted C007 reliability/ownership harnesses.
- Phase 8 depends on every selected story and acceptance task.

### User Story Dependencies

- **US1**: Starts after foundational fixtures; produces the callable product surface.
- **US2**: Starts after US1 contract shape is known; consumes upstream controls and adapters.
- **US3**: Starts after US1 and promoted host contracts; exercises shared state and approval isolation.
- **US4**: Starts after US1-US3; composes them into complete journeys.
- **US5**: Starts after US1-US4; completes the AT matrix and evidence package.

### Parallel Opportunities

- T007 and T008 can run in parallel after T006.
- T011 and T012 can run in parallel.
- T018 and T019 can run in parallel.
- T033, T034, and T035 can run in parallel.
- T042 and T047 can run in parallel after preceding story gates.

## Implementation Strategy

1. Open the dependency gate and record the exact promoted SHA.
2. Build the smallest guarded surface and prove forbidden paths are absent.
3. Add the single shared behavior source and cross-host safety checks.
4. Add four readable scenario fixtures rather than a scenario framework.
5. Fill the AT-01 through AT-16 matrix and evidence metadata.
6. Run targeted, full, static/type, smoke, live-host, adversarial, and offline verification in proportion to available proven capabilities.

## Traceability Summary

| Requirement Group | Primary Tasks |
|---|---|
| FR-001 to FR-003 | T011-T017 |
| FR-004 to FR-006 | T018-T026 |
| FR-007 | T027-T032 |
| FR-008 | T033-T041 |
| FR-009 to FR-011 | T006-T010, T049-T054 |
| FR-012 to FR-017 | T042-T054 |
| FR-018 | T001-T003, T056, T060 |
| FR-019 | T003, T021 |
| SC-001 to SC-010 | T009-T010, T017, T022, T026, T032, T041, T047-T054 |

## Notes

- Tests accompany each behavior slice but strict Red-Green-Refactor orchestration is not required.
- Do not change an upstream experiment or product rule to make acceptance pass.
- Do not edit integration/orchestration records or final release documentation from this branch.
- Every new executable Python file must begin with its interpreter directive and a brief purpose comment, consistent with repository instructions.
