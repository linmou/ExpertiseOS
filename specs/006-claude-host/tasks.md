# Tasks: Claude Code Host Adapter

**Intent**: Implement and verify the Claude adapter in dependency order without duplicating shared domain behavior.

**Input**: Design documents from `specs/006-claude-host/`
**Prerequisites**: Approved C001-C004 integration promotion SHA, especially passed Claude G0 evidence

## Format: `[ID] [P?] [Story] Description`

- **[P]**: May proceed in parallel because it owns a different file and has no incomplete dependency.
- **[Story]**: Maps the task to a user story in `spec.md`.
- New Python files begin with a shebang and a brief purpose comment; new tests also identify the production file and behavior they cover.

## Phase 1: Upstream and Evidence Gate

**Purpose**: Prevent implementation against guessed host mechanisms or stale contracts.

- [ ] T001 Record the immutable integration promotion SHA and C001-C004 contract-shape verification in `specs/006-claude-host/implementation-evidence.md`
- [ ] T002 Validate C001 Claude evidence contains exact host version, OS, permission mode, public registration/uninstall path, event names, session identity, actual-user proof, and failure-open result before enabling any capability in `tests/fixtures/claude_code/`
- [ ] T003 [P] Add sanitized passed and unavailable capability/event fixtures, with no unrelated prompt or candidate content, in `tests/fixtures/claude_code/`
- [ ] T004 Stop write-capable implementation as an explicit component blocker if T002 lacks passed actual-user decision evidence; otherwise record the supported matrix used by tests in `tests/fixtures/claude_code/README.md`

**Checkpoint**: Exact host inputs and upstream boundaries are known; no support claim is inferred.

---

## Phase 2: Foundational Contract Checks

**Purpose**: Freeze Claude-specific expectations before implementing the adapter.

- [ ] T005 Create contract cases for supported/unsupported capability truthfulness and exact environment matching in `tests/contract/test_claude_code_adapter.py`
- [ ] T006 Add lifecycle cases for start, normalized supported events, nested atomic depth, eligible/ineligible checkpoints, end, and invalid ordering in `tests/contract/test_claude_code_adapter.py`
- [ ] T007 Add decision cases for Save, Skip, final/non-final Edit, ambiguity, quotes, generic permission, assistant/tool/model origins, stale/changed/cross-session/cross-host bindings, direct-save bounds, and unrelated-event expiry in `tests/contract/test_claude_code_adapter.py`
- [ ] T008 Add failure cases proving service exceptions, timeouts, malformed results, and every non-`committed` result preserve host continuation and never render Saved in `tests/contract/test_claude_code_adapter.py`

**Checkpoint**: Tests cover the required contract and negative boundaries using sanitized fixtures.

---

## Phase 3: User Story 1 - Start expertiseOS in Claude Code (Priority: P1)

**Goal**: Activate and remove the proven Claude integration safely with truthful capabilities.

**Independent Test**: A fresh pinned fixture activates against the shared service, preserves unrelated configuration, and removes only expertiseOS-owned registration.

- [ ] T009 [US1] Implement exact-environment capability selection and `can_write` dependency on passed decision evidence in `src/expertiseos/hosts/claude_code.py`
- [ ] T010 [US1] Implement the C001-proven public registration, activation, health-check, and uninstall translation while preserving unrelated configuration in `src/expertiseos/hosts/claude_code.py`
- [ ] T011 [US1] Complete onboarding and capability fixture assertions, including unsupported/read-only outcomes, in `tests/contract/test_claude_code_adapter.py`

**Checkpoint**: Setup behavior is reversible and capability claims match evidence.

---

## Phase 4: User Story 2 - Continue Work Through Safe Checkpoints (Priority: P1)

**Goal**: Normalize lifecycle events without interrupting ordinary Claude work.

**Independent Test**: A bounded operation emits no eligible prompt until depth zero and a supported checkpoint; service failure leaves the host result intact.

- [ ] T012 [US2] Implement session start/end validation, raw supported-event normalization, and terminal cleanup in `src/expertiseos/hosts/claude_code.py`
- [ ] T013 [US2] Implement nonnegative atomic-depth tracking, comparison-due marking, and conservative checkpoint eligibility in `src/expertiseos/hosts/claude_code.py`
- [ ] T014 [US2] Consume C004 control and exclusion results before forwarding source context or enabling collection, exercise, and recall interactions in `src/expertiseos/hosts/claude_code.py`
- [ ] T015 [US2] Add host-continuation handling for service and retrieval failures with no false memory success in `src/expertiseos/hosts/claude_code.py`
- [ ] T016 [US2] Verify lifecycle, control/exclusion, and failure behavior against the shared service in `tests/integration/test_claude_code_service.py`

**Checkpoint**: Event flow is host-neutral downstream, control-correct, and failure-open for work.

---

## Phase 5: User Story 3 - Authorize an Exact Proposal (Priority: P1)

**Goal**: Produce a grant-eligible observation only from one exact actual-user decision.

**Independent Test**: One matching Save reaches C002 and commits once; every adversarial or stale fixture produces no grant and no write.

- [ ] T017 [US3] Implement deterministic Save/Skip/final-content Edit observation against one C001 `DecisionBinding` in `src/expertiseos/hosts/claude_code.py`
- [ ] T018 [US3] Implement unrelated-event/session-end expiry and fresh-digest re-display requirements without persisting adapter recovery state in `src/expertiseos/hosts/claude_code.py`
- [ ] T019 [US3] Implement narrow same-event direct-save observation for deterministically identified material and require a later proposal decision for every semantic ambiguity in `src/expertiseos/hosts/claude_code.py`
- [ ] T020 [US3] Pass actual adapter observations through the real C002 registration/commit path and verify exact-once success plus forged/stale/cross-origin rejection in `tests/integration/test_claude_code_service.py`

**Checkpoint**: The Claude adapter proves the actual-user boundary without owning grants or approval policy.

---

## Phase 6: User Story 4 - Recall Shared Approved Knowledge Safely (Priority: P2)

**Goal**: Consume shared approved state without transferring authorization or authority.

**Independent Test**: Claude receives the actual C003-produced object and C004 permissions while cross-host approval and stale writes fail.

- [ ] T021 [US4] Consume only bounded C003 service retrieval responses and preserve stable identity, version, provenance, conflicts, health, exclusions, and untrusted labeling in `src/expertiseos/hosts/claude_code.py`
- [ ] T022 [US4] Verify the real C003 producer output reaches the adapter unchanged and C004 permissions gate observation/recall correctly in `tests/integration/test_claude_code_service.py`
- [ ] T023 [US4] Verify another host/session cannot authorize a Claude proposal and stale expected versions return conflict without overwrite or Saved rendering in `tests/integration/test_claude_code_service.py`
- [ ] T024 [US4] Verify host switching, retrieval, task completion, and assistant output make zero learner-evidence or mastery mutation calls in `tests/integration/test_claude_code_service.py`

**Checkpoint**: Shared approved state works while proposals and grants remain session/adapter scoped.

---

## Phase 7: Live Host and Component Gates

**Purpose**: Prove the claimed Claude support surface on the pinned environment.

- [ ] T025 Add a marker-gated pinned live-host fixture for activation, checkpoint safety, actual-user Save, model-only rejection, candidate expiry, service outage, and capability reporting in `tests/e2e/test_claude_code_live.py`
- [ ] T026 Run `pytest tests/contract/test_claude_code_adapter.py -q` and retain the full command, environment, exit status, and test log path in `specs/006-claude-host/implementation-evidence.md`
- [ ] T027 Run `pytest tests/integration/test_claude_code_service.py -q` with actual C001-C004 producer objects and retain the full command, integration SHA, exit status, and test log path in `specs/006-claude-host/implementation-evidence.md`
- [ ] T028 Run `pytest tests/e2e/test_claude_code_live.py -q --run-live-claude` on the exact supported environment and retain sanitized input-output pairs, host metadata, exit status, and limitations in `specs/006-claude-host/implementation-evidence.md`
- [ ] T029 Run `mypy src/expertiseos/hosts/claude_code.py tests/contract/test_claude_code_adapter.py tests/integration/test_claude_code_service.py` and retain the result in `specs/006-claude-host/implementation-evidence.md`
- [ ] T030 Run `ruff check src/expertiseos/hosts/claude_code.py tests/contract/test_claude_code_adapter.py tests/integration/test_claude_code_service.py tests/e2e/test_claude_code_live.py` and retain the result in `specs/006-claude-host/implementation-evidence.md`
- [ ] T031 Run the affected repository smoke suite and verify no candidate marker appears in expertiseOS-controlled durable stores after Skip, unrelated input, session end, or restart; retain commands and evidence in `specs/006-claude-host/implementation-evidence.md`

---

## Dependencies & Execution Order

- Phase 1 requires the approved integration promotion SHA and blocks every implementation task.
- Phase 2 depends on Phase 1 evidence and defines all contract expectations.
- US1 establishes environment capabilities and activation before runtime behavior is accepted.
- US2 establishes lifecycle/control/failure foundations used by US3 and US4.
- US3 depends on US2 session and checkpoint state plus C002 availability.
- US4 depends on US2 service/control handling plus C003/C004 availability; it may be implemented in parallel with US3 after US2.
- Live-host and final component gates depend on all selected stories.

## Parallel Opportunities

- T003 can prepare sanitized fixture data while T001 verifies contract shapes.
- After US2, US3 decision binding and US4 retrieval integration touch distinct methods/tests but share production ownership; execute serially within this single-owner worktree to avoid conflicts.
- Static checks T029 and T030 may run after implementation is stable; verification evidence must refer to the same commit.

## Implementation Strategy

1. Prove support inputs before production code.
2. Build one thin adapter against integrated upstream contracts.
3. Verify lifecycle and failure behavior before enabling decisions.
4. Enable writes only after exact actual-user evidence and C002 integration pass.
5. Add shared retrieval consumption and run the pinned live-host gate.

No backward-compatibility layer, generic host framework, scheduler, adapter database, or duplicate domain logic is included.
