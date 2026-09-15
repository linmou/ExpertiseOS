# Tasks: Learner Evidence and Learning Controls

**Intent**: Provide a dependency-ordered, requirement-complete implementation checklist with focused negative and integration verification.

**Input**: Design documents from `/specs/004-learning-controls/`
**Prerequisites**: C002 approval/state promotion and C003 retrieval-contract promotion before integration tasks

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes a different file and has no dependency on an incomplete task.
- **[Story]**: Maps the task to one user story in `spec.md`.
- Every new Python test file begins with a comment naming its responsible production file and purpose.
- Every new Python code file begins with a Python shebang and a comment stating its purpose.

## Phase 1: Setup and Contract Confirmation

**Purpose**: Confirm promoted dependencies and freeze boundary fixtures before component code.

- [x] T001 Verify C002 guarded mutation, receipt, expected-version, and state adapter names against `specs/004-learning-controls/contracts/sqlite-schema-request.md` and record its exact promotion SHA in `specs/004-learning-controls/verification.md`
- [x] T002 Verify C003 approved object ID/version/scope/conflict facts against `specs/004-learning-controls/contracts/learning-controls.md` and record its exact promotion SHA in `specs/004-learning-controls/verification.md`
- [x] T003 Add approved-object, approval-receipt, evidence, and control-time fixtures without candidate persistence in `tests/unit/learning_fakes.py`
- [x] T004 Create boundary tests proving unapproved/stale mutations never call the state port and missing producer facts fail explicitly in `tests/contract/test_learning_boundaries.py`

**Checkpoint**: Upstream contracts are concrete and the contract tests are initially failing for missing C004 behavior.

---

## Phase 2: Foundational Learning Types and Validation

**Purpose**: Establish direct immutable records and shared validation used by every story.

- [x] T005 Define evidence, summary, approved-object-fact, and inspection records with no dataclass definition defaults in `src/expertiseos/learning/evidence.py`
- [x] T006 [P] Define advancement thresholds, settings, progress, exclusion, deferred-activity, response/activity facts, and control-resolution records with no dataclass definition defaults in `src/expertiseos/learning/controls.py`
- [x] T007 Implement nonblank, enum, positive version, bounded limit, timezone, approved-reference, and positive nondecreasing threshold validation including autonomous minimum two in `src/expertiseos/learning/evidence.py` and `src/expertiseos/learning/controls.py`
- [x] T008 Complete contract tests for receipt-required persistence, exact object/version binding, state-port idempotency keys, and fail-open host-work semantics in `tests/contract/test_learning_boundaries.py`

**Checkpoint**: Stories can use stable validated inputs without adding a new service, repository layer, or policy engine.

---

## Phase 3: User Story 1 - Approve Evidence and Inspect Mastery (Priority: P1)

**Goal**: Persist only approved attributable evidence and inspect state with its supporting history.

**Independent Test**: Approved user evidence changes the version/scope summary; save-only, assistant-only, unknown-contribution, self-report, rejection, and inapplicable evidence do not.

### Tests for User Story 1

- [x] T009 [P] [US1] Add evidence validation tests proving only pass advances while partial/fail/insufficient remain inspectable with zero contribution, plus rejected/corrected proposals, missing receipts, assistant-only output, unknown contribution, self-report, and retrieval non-evidence in `tests/unit/test_learner_evidence.py`
- [x] T010 [P] [US1] Add mastery tests for `new` through `transferred`, explicit `1,1,1,1,2` thresholds, alternate valid thresholds, stronger evidence skipping elementary stages, monotonic append behavior, and no advancement from save/retrieval in `tests/unit/test_mastery_transitions.py`
- [x] T011 [P] [US1] Add version/scope applicability, revised-boundary history retention, insufficient-evidence, and bounded support-list tests in `tests/unit/test_mastery_transitions.py`
- [x] T012 [P] [US1] Add bounded inspection tests for supporting/excluded evidence and invalid limits in `tests/unit/test_inspection.py`

### Implementation for User Story 1

- [x] T013 [US1] Implement evidence eligibility and exact approved-object/version/scope validation in `src/expertiseos/learning/evidence.py`
- [x] T014 [US1] Implement pass-only deterministic `new` through `transferred` summary rules using validated thresholds with supporting and excluded evidence IDs in `src/expertiseos/learning/evidence.py`
- [x] T015 [US1] Implement bounded learning-state inspection projections without durable side effects in `src/expertiseos/learning/evidence.py`
- [x] T016 [US1] Run the US1 unit and boundary tests and record the exact command/result in `specs/004-learning-controls/verification.md`

**Checkpoint**: FR-001 through FR-006, FR-008, and the learner portion of FR-020 are independently verified.

---

## Phase 4: User Story 2 - Reach Mastery Deterministically (Priority: P1)

**Goal**: Assign autonomous only when every approved pilot condition is satisfied.

**Independent Test**: The complete fixture yields autonomous and removing each condition separately withholds it with an inspectable unmet reason.

### Tests for User Story 2

- [x] T017 [US2] Add complete autonomous and one-missing-condition cases for configured pass count, minimum two, independence, task identity, session identity, transfer, contradiction, and agreement, proving numeric configuration cannot bypass safeguards in `tests/unit/test_autonomy_heuristic.py`
- [x] T018 [US2] Add cases for duplicate evidence IDs, partial/fail/insufficient outcomes, known assistance, scope mismatch, and repeated same-task success in `tests/unit/test_autonomy_heuristic.py`

### Implementation for User Story 2

- [x] T019 [US2] Implement the literal autonomous predicate, threshold minimum, non-numeric guards, and unmet-condition reporting without scores in `src/expertiseos/learning/evidence.py`
- [x] T020 [US2] Integrate autonomous evaluation into the deterministic mastery summary while preserving contradiction and agreement inputs in `src/expertiseos/learning/evidence.py`
- [x] T021 [US2] Run the US2 tests plus US1 regression tests and append the exact command/result to `specs/004-learning-controls/verification.md`

**Checkpoint**: FR-007 and SC-003 are independently verified without psychometric behavior.

---

## Phase 5: User Story 3 - Control Learning Without Blocking Work (Priority: P1)

**Goal**: Resolve target, fatigue, pause, disable, exclusions, and period boundaries into explicit permissions.

**Independent Test**: Every state combination returns the required observation, collection, exercise, and recall permissions and preserves ordinary host work.

### Tests for User Story 3

- [x] T022 [P] [US3] Add pairwise and all-active precedence tests for disabled, pause, fatigue rest, target satisfied, and active behavior in `tests/unit/test_pause_disable.py`
- [x] T023 [P] [US3] Add target-versus-fatigue tests for target preservation, no final exercise, configured/user rest duration, expired rest, and local daily/weekly rollover in `tests/unit/test_target_vs_fatigue.py`
- [x] T024 [P] [US3] Add effort boundary tests for 0, 0.25, 1.0, 2.0, highest-only classification, ordinary task/model output, duplicate event, and effort-limit transition in `tests/unit/test_effort_limit.py`
- [x] T025 [P] [US3] Add literal source/path/session exclusion tests including canonical paths, nonmatching scopes, before-observation decisions, and before-retrieval decisions in `tests/unit/test_scope_exclusions.py`
- [x] T026 [P] [US3] Add control inspection tests for bounded exclusions/progress, active reason, and expiry in `tests/unit/test_inspection.py`

### Implementation for User Story 3

- [x] T027 [US3] Implement daily/weekly period keys and explicit default-setting constructors using local device timezone in `src/expertiseos/learning/controls.py`
- [x] T028 [US3] Implement highest-only effort classification and fatigue transition intent with stable event IDs in `src/expertiseos/learning/controls.py`
- [x] T029 [US3] Implement exact control precedence and the four separate permission outputs in `src/expertiseos/learning/controls.py`
- [x] T030 [US3] Implement literal source/path/session exclusion matching and bounded control inspection projections in `src/expertiseos/learning/controls.py`
- [x] T031 [US3] Expose explicit candidate-expiry intent for fatigue without importing or modifying the upstream candidate lifecycle in `src/expertiseos/learning/controls.py`
- [x] T032 [US3] Run US3 tests, all prior unit tests, and boundary regressions and append exact results to `specs/004-learning-controls/verification.md`

**Checkpoint**: FR-009 through FR-012 and FR-014 through FR-020 are independently verified.

---

## Phase 6: User Story 4 - Count Reflection and Defer Approved Work (Priority: P2)

**Goal**: Count qualifying approved reflection once and persist only minimal approved-object deferred references.

**Independent Test**: Eligible reflections count once across output multiplicity/retry; invalid reflections and deferred free-form/unapproved content are rejected.

### Tests for User Story 4

- [x] T033 [P] [US4] Add qualifying-reflection tests for meaningful contribution, reusable knowledge, approved connection/save, linked outputs, duplicates, paraphrase, relabeling, raw logs, and assistant-only output in `tests/unit/test_reflection_counting.py`
- [x] T034 [P] [US4] Add deferred creation/removal tests for explicit decision, nonempty approved versioned references, free-form content rejection, missing/stale objects, duplicate ID, later session, foreground requirement, and every inactive control reason in `tests/unit/test_deferred_learning.py`

### Implementation for User Story 4

- [x] T035 [US4] Implement pure reflection qualification and one-event progress intent in `src/expertiseos/learning/controls.py`
- [x] T036 [US4] Implement minimal deferred-activity validation, active-foreground offer eligibility, and removal intent in `src/expertiseos/learning/controls.py`
- [x] T037 [US4] Run US4 and full component unit/contract tests and append exact results to `specs/004-learning-controls/verification.md`

**Checkpoint**: FR-013 and FR-021 through FR-023 are independently verified.

---

## Phase 7: Shared SQLite and Real Producer-Consumer Integration

**Purpose**: Prove the component against the promoted approval/state and retrieval implementations without taking shared-file ownership.

- [ ] T038 Send C002 the exact logical schema/state-operation request in `specs/004-learning-controls/contracts/sqlite-schema-request.md` and record the accepted implementation SHA in `specs/004-learning-controls/verification.md`
- [ ] T039 Add integration tests using the real C002 state adapter and C003 approved object facts for fresh migration, restart, receipt binding, version/scope filtering, and unavailable-state failure in `tests/integration/test_learning_state_sqlite.py`
- [ ] T040 Add integration tests for threshold persistence/update validation, duplicate evidence/reflection/effort delivery from distinct hosts, stale control versions, atomic counter failures, bounded inspection, and deferred schema without free-form content in `tests/integration/test_learning_state_sqlite.py`
- [ ] T041 Run `tests/integration/test_learning_state_sqlite.py` with the actual producer artifacts and record command, exit code, dependency SHAs, and result in `specs/004-learning-controls/verification.md`
- [ ] T042 Provide C005-C008 with the tested control/inspection contract and integration SHA through the integration owner's edge packet, referencing `specs/004-learning-controls/contracts/learning-controls.md`

**Checkpoint**: FR-024, SC-004 through SC-006, and the C002/C003 handoffs are proven with real artifacts.

---

## Phase 8: Verification and Handoff

**Purpose**: Close component quality gates and provide reproducible downstream evidence.

- [x] T043 Run the full repository test suite after all component code changes and record failures by owning component in `specs/004-learning-controls/verification.md`
- [x] T044 Run mypy for all modified production and test paths and record the exact result in `specs/004-learning-controls/verification.md`
- [x] T045 Run repository lint/format checks for all modified paths and record the exact result in `specs/004-learning-controls/verification.md`
- [x] T046 Verify no pending candidate content, alternate approval path, summary cache, background worker, policy engine, scheduler, scoring model, or shared-file ownership drift exists and record the review in `specs/004-learning-controls/verification.md`
- [x] T047 Map green evidence to FR-001 through FR-025, SC-001 through SC-009, AT-07, AT-09, AT-10, AT-11, and learning portions of AT-12/AT-15 in `specs/004-learning-controls/verification.md`
- [x] T048 Commit the locally verified component, report the immutable SHA to integration, and remain assigned for component-local integration regressions in `specs/004-learning-controls/verification.md`

---

## Dependencies & Execution Order

- Phase 1 depends on promoted C002 and C003 contracts.
- Phase 2 depends on Phase 1 contract confirmation.
- US1 and US3 types can be prepared in parallel after Phase 2; implementation remains single-owner and file conflicts are serialized.
- US2 depends on US1's evidence eligibility and summary behavior.
- US4 depends on US3's control resolution for offer eligibility.
- SQLite integration depends on all stories plus the C002-owned migration implementation.
- Final verification depends on all component and integration checks.

## Parallel Opportunities

- T005 and T006 touch separate owned modules.
- Test files marked `[P]` can be authored independently before their corresponding implementation task.
- C002 schema implementation and C004 pure behavior can proceed under separate stable owners after the contract is accepted.

## Implementation Strategy

1. Stabilize real upstream names before writing adapters.
2. Deliver US1 and US2 as the evidence/mastery core.
3. Deliver US3 before any proactive learning consumer uses controls.
4. Add the minimal US4 reflection/defer behavior.
5. Integrate once through C002/C003 and promote that exact green SHA downstream.

## Task Summary

- Total tasks: 48
- Setup/foundational: 8
- US1: 8
- US2: 5
- US3: 11
- US4: 5
- Integration/handoff: 11
- Suggested first independently useful scope: US1 plus US2
- Format: all tasks use checkbox, sequential ID, required story label, and exact file path
