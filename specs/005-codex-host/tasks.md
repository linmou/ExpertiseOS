# Tasks: Codex Host Adapter

**Input**: Design documents from `/specs/005-codex-host/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required by FR-019 and the MVP acceptance plan. Build each behavior with its focused tests and run the listed verification checkpoint before moving on; strict multi-agent TDD orchestration is not required.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel because it owns a different file and has no dependency on an incomplete task.
- **[Story]**: Maps implementation work to the independently testable user story.
- Every implementation and test path is explicit; new Python files start with a shebang and a one-line purpose comment, and each test file begins with the responsible production file and test purpose.

## Phase 1: Setup and Evidence Intake

**Purpose**: Refuse speculative host bindings and establish exact promoted dependencies before code work.

- [ ] T001 Record the promoted integration SHA and verify C001 HostAdapter, C002 approval/proposal, C003 retrieval/degradation, and C004 controls/exclusions contract paths against `specs/005-codex-host/contracts/codex-adapter.md`
- [ ] T002 Validate the immutable G0 packet field-by-field against `specs/005-codex-host/contracts/g0-evidence.md` and record each supported/unsupported Codex capability in `specs/005-codex-host/evidence/g0-validation.md`
- [ ] T003 [P] Materialize only the redacted, reproducible G0 Codex event payloads needed by claimed capabilities in `tests/fixtures/codex/g0_events.json` and record provenance plus exact version/OS/permission metadata in `tests/fixtures/codex/README.md`
- [ ] T004 Reconcile promoted upstream names and signatures with `specs/005-codex-host/contracts/codex-adapter.md`; route any semantic mismatch back to integration before editing production code

**Checkpoint**: Exact host mechanism, version, event provenance, checkpoints, and capability limits are evidenced; missing evidence is explicitly false/read-only.

---

## Phase 2: Foundational Codex Translation

**Purpose**: Establish one thin adapter surface used by every story without duplicating upstream domain behavior.

- [ ] T005 Define Codex payload-to-normalized-event mapping and minimal session-state construction in `src/expertiseos/hosts/codex.py`, using explicit initialization for every dataclass field and adding no defaults to dataclass definitions (FR-004, FR-005)
- [ ] T006 Implement evidence-backed capability snapshot construction and environment matching in `src/expertiseos/hosts/codex.py`, defaulting every unproven capability to false (FR-003, FR-018)
- [ ] T007 Implement exception containment around adapter-to-service calls in `src/expertiseos/hosts/codex.py` so expertiseOS failures return non-owning degradation outcomes and never intercept ordinary host work (FR-017)
- [ ] T008 [P] Add normalized-event and session-identity contract coverage, including malformed/wrong-session payloads, in `tests/contract/test_codex_host_contract.py` (FR-004, FR-005)
- [ ] T009 [P] Add per-capability evidence matching, unsupported-version, wrong-OS, wrong-permission, and partial-capability coverage in `tests/contract/test_codex_capabilities.py` (FR-003, FR-018)
- [ ] T010 Run targeted foundational contract tests and mypy for `src/expertiseos/hosts/codex.py`, saving command, full result, environment metadata, and exit code in `specs/005-codex-host/evidence/foundation-verification.md`

**Checkpoint**: The adapter translates only verified payloads, exposes no optimistic capabilities, and has no durable or domain-owned state.

---

## Phase 3: User Story 1 - Onboard a Supported Codex Host (Priority: P1)

**Goal**: Consent, register, activate, health-check, and reversibly uninstall the exact supported local Codex integration without damaging unrelated configuration.

**Independent Test**: Complete setup in the pinned fresh environment, start a new session, inspect capabilities/service connection, then uninstall and compare unrelated configuration byte-for-byte.

- [ ] T011 [US1] Implement the G0-proven consent-before-registration, configuration-preserving install, health-check, automatic-activation, and reversible removal path directly in `src/expertiseos/hosts/codex.py` unless the promoted host contract requires a distinct existing onboarding path (FR-001, FR-002)
- [ ] T012 [US1] Implement minimal bounded startup loading of capability and upstream control state in `src/expertiseos/hosts/codex.py`, without loading repository/vault content or requesting a second model key (FR-001, FR-016)
- [ ] T013 [P] [US1] Add fresh/supported, unsupported, consent-declined, partial-capability, existing-config preservation, health-failure, and reversible-uninstall contract cases in `tests/contract/test_codex_onboarding.py` (FR-001, FR-002, FR-003)
- [ ] T014 [US1] Add and run the pinned onboarding/activation/uninstall live harness in `tests/e2e/test_codex_live_host.py`, then record exact inputs, outputs, hashes, version/OS/permission mode, and exit result in `specs/005-codex-host/evidence/live-onboarding.md` (SC-001, SC-008)

**Checkpoint**: A supported fresh session activates only after consent; unsupported claims remain unavailable and uninstall is reversible.

---

## Phase 4: User Story 2 - Work Without Unsafe Interruption (Priority: P1)

**Goal**: Defer expertiseOS interactions until a verified safe checkpoint, honor controls/exclusions before forwarding content, and preserve Codex task completion during failures.

**Independent Test**: Exercise nested/unbalanced atomic fixtures, exclusions/disable states, and service failures while confirming task output completes and no early prompt or false save appears.

- [ ] T015 [US2] Implement G0-proven atomic begin/end and conservative safe-checkpoint translation with non-negative nesting/unknown-state protection in `src/expertiseos/hosts/codex.py` (FR-006)
- [ ] T016 [US2] Implement comparison-due coalescing so low-level events defer at most one comparison request to the next eligible boundary and never invoke semantic analysis per event in `src/expertiseos/hosts/codex.py` (FR-007)
- [ ] T017 [US2] Apply promoted disable/pause/fatigue/target and source/path/session exclusion results before observation, candidate forwarding, retrieval, or proposal prompting in `src/expertiseos/hosts/codex.py` (FR-008)
- [ ] T018 [P] [US2] Add normal, nested, unbalanced, missing-boundary, delayed-comparison, and unresolved-proposal checkpoint cases in `tests/contract/test_codex_safe_checkpoint.py` (FR-006, FR-007)
- [ ] T019 [P] [US2] Add disabled and source/path/session exclusion tests that assert prohibited content never reaches adapter service calls in `tests/contract/test_codex_scope_controls.py` (FR-008)
- [ ] T020 [US2] Add service, search, timeout, and rejected-write failure cases proving ordinary task callbacks/results continue and no Saved result is synthesized in `tests/integration/test_codex_service_failure.py` (FR-017)
- [ ] T021 [US2] Run focused checkpoint/control/failure tests and mypy, then record commands, full results, and exit codes in `specs/005-codex-host/evidence/work-continuity-verification.md` (SC-002, SC-005)

**Checkpoint**: No proactive interaction occurs inside an unsafe operation, excluded content is not forwarded, and host work remains independent of expertiseOS health.

---

## Phase 5: User Story 3 - Authorize an Exact Proposal (Priority: P1)

**Goal**: Convert only one fresh, unambiguous actual-user response to one active proposal into the exact upstream decision/decline action.

**Independent Test**: Run Save/Edit/Skip plus every adversarial event source and binding mismatch, asserting the upstream fake records exactly the permitted call and no others.

- [ ] T022 [US3] Implement actual-user provenance validation at the G0-proven Codex event entrypoint in `src/expertiseos/hosts/codex.py`, making non-user payloads structurally unable to call decision registration (FR-009)
- [ ] T023 [US3] Implement single-active-proposal Save and Skip/cancel routing with unchanged proposal/session/adapter/digest/event/version fields into promoted C002 interfaces in `src/expertiseos/hosts/codex.py` (FR-010, FR-011)
- [ ] T024 [US3] Implement Edit-with-final-content replacement/re-display and Edit-without-final-content no-grant behavior in `src/expertiseos/hosts/codex.py` (FR-012)
- [ ] T025 [US3] Implement unrelated-message expiry, ambiguous-response rejection, multiple-proposal disambiguation, and narrowly deterministic direct-save routing through the normal proposal/grant path in `src/expertiseos/hosts/codex.py` (FR-013, FR-014)
- [ ] T026 [P] [US3] Add Save, Skip, both Edit forms, direct-save eligible/ineligible, duplicate event, multiple-proposal, and unrelated-message coverage in `tests/contract/test_codex_user_event_binding.py` (FR-010 through FR-014)
- [ ] T027 [P] [US3] Add adversarial model-argument, assistant-text, tool-output, generic-permission, quoted-Save, stale-proposal, wrong-session/adapter, changed-digest, changed-version, and replay cases in `tests/contract/test_codex_user_event_binding.py` (FR-009 through FR-014)
- [ ] T028 [US3] Run decision-binding contract tests and the G0 actual-user live fixture, then record input-output pairs, grant/write counts, commands, hashes, and exit results in `specs/005-codex-host/evidence/user-decision-verification.md` (SC-003, SC-004)

**Checkpoint**: Valid Save produces at most one exact upstream decision; every non-user, ambiguous, stale, or mismatched case produces zero grants and zero writes.

---

## Phase 6: User Story 4 - Share Local State Without Sharing Authorization (Priority: P2)

**Goal**: Use the shared approved service state while keeping pending authorization isolated and cleaning all volatile state at session end.

**Independent Test**: Retrieve a stable approved object through Codex, reject foreign/stale decisions through upstream services, and terminate the session with no unresolved adapter/candidate/grant state.

- [ ] T029 [US4] Route approved reads, bounded search, controls, and guarded mutation proposals only through the promoted shared local service interfaces in `src/expertiseos/hosts/codex.py` (FR-016)
- [ ] T030 [US4] Implement session-end upstream expiry and local teardown for active proposal references, unused grants, comparison state, user-event references, and suppression state in `src/expertiseos/hosts/codex.py` (FR-015)
- [ ] T031 [P] [US4] Add session-end, abrupt-end, late-event, repeated-end, and fresh-session isolation cases in `tests/contract/test_codex_session_expiry.py` (FR-015)
- [ ] T032 [US4] Add shared approved read identity and cross-session/cross-host/stale-write rejection handoff cases using actual promoted service outputs in `tests/integration/test_codex_shared_service.py` (FR-016)
- [ ] T033 [US4] Run session/shared-service tests and candidate marker persistence audit, recording store locations checked, commands, complete results, and exit codes in `specs/005-codex-host/evidence/shared-state-verification.md` (SC-006, SC-007)

**Checkpoint**: Approved state is shared by stable identity; authorization and volatile state remain session-bound and disappear at end.

---

## Phase 7: Full Codex Verification and Handoff

**Purpose**: Prove the component contract and provide integration-owned documentation with complete evidence, without editing shared release files.

- [ ] T034 Run the complete component pytest suite plus repository lint, static checks, and mypy for all modified production and test paths, recording commands and full results in `specs/005-codex-host/evidence/component-verification.md`
- [ ] T035 Run the pinned live Codex matrix for activation, bounded startup, atomic checkpoint, Save, Edit then Save, Skip, unrelated expiry, forged/model-only approval, session cleanup, outage, shared retrieval, and degradation in `tests/e2e/test_codex_live_host.py`, preserving complete metadata and input-output evidence under `specs/005-codex-host/evidence/live-matrix/`
- [ ] T036 Verify every FR-001 through FR-019 and SC-001 through SC-008 maps to passing evidence and record capability limits plus downstream C008 handoff paths in `specs/005-codex-host/evidence/traceability.md`
- [ ] T037 Commit the clean component package, report the immutable component SHA and verification commands to integration, and leave shared `docs/`, `skill/SKILL.md`, service wiring, orchestration records, and integration worktree untouched

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup and Evidence Intake** blocks all code work; it requires promoted C001-C004 contracts and immutable G0 evidence.
- **Foundational Translation** depends on Setup and blocks all user stories.
- **US1 Onboarding** and **US2 Work Continuity** may proceed after foundation where their files/tests do not conflict; one owner should serialize edits to `hosts/codex.py`.
- **US3 Exact Proposal Authorization** depends on foundation and promoted C002 proposal/grant APIs; it does not depend on onboarding UI behavior.
- **US4 Shared State** depends on foundation plus promoted C002-C004 service interfaces; final shared-service checks use real upstream outputs.
- **Full Verification and Handoff** depends on all desired stories.

### User Story Dependencies

```text
G0 + promoted C001-C004
  -> foundational Codex translation
       -> US1 onboarding/activation
       -> US2 checkpoints/continuity
       -> US3 actual-user decisions
       -> US4 shared reads/session isolation
            -> full live matrix -> C008 integration
```

### Parallel Opportunities

- Fixture provenance intake T003 can run while contract reconciliation T004 is reviewed.
- Contract test files T008/T009, T018/T019, and T026/T027 are independent file/scope groups after their corresponding production contract is stable.
- Live fixtures are serial against one pinned Codex environment to avoid session/config interference.
- No two tasks concurrently edit `src/expertiseos/hosts/codex.py`.

## Implementation Strategy

1. Stop immediately if G0 cannot prove actual-user provenance; implement only the accurately reported read-only capability set.
2. Build the minimal translation and capability foundation.
3. Complete each story with focused negative-path and integration verification.
4. Run the whole component and pinned live-host matrix.
5. Hand the immutable verified component commit to C008; do not add cross-host glue locally.

## Coverage Map

| Requirement group | Tasks |
|---|---|
| FR-001 to FR-003 | T002-T003, T006, T009, T011-T014 |
| FR-004 to FR-005 | T005, T008, T010 |
| FR-006 to FR-008 | T015-T021 |
| FR-009 to FR-014 | T022-T028 |
| FR-015 to FR-016 | T029-T033 |
| FR-017 to FR-018 | T002, T006-T010, T020-T021 |
| FR-019 and SC-001 to SC-008 | T014, T021, T028, T033-T036 |
