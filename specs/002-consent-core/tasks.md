# Tasks: Consent Core

**Input**: Design documents from `/specs/002-consent-core/`  
**Prerequisites**: C001 package/bootstrap, host/backend contracts, and fakes; `plan.md`, `spec.md`, `research.md`, `data-model.md`, and `contracts/`

**Verification approach**: Implement in small task groups, then run the named focused checks. Tests include happy paths, lifecycle boundaries, forged authorization, stale versions, restart loss, and interrupted writes; this is task-based development rather than the strict multi-agent TDD workflow. Every new Python code file begins with a shebang and a concise purpose comment. Every new test also begins with a comment naming the production file and behavior it verifies.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can proceed concurrently because it owns different files and has no dependency on incomplete work.
- **[Story]**: Maps work to the independently testable user story in `spec.md`.
- Every implementation task includes its concrete file path and requirement mapping.

## Phase 1: Setup and Upstream Contract Check

**Purpose**: Verify the C001 baseline before creating component code.

- [ ] T001 Inspect C001's model-library choice, package layout, Python configuration, and test commands in `pyproject.toml` and record compatible implementation constraints in `specs/002-consent-core/quickstart.md` (FR-001, SC-008)
- [ ] T002 Inspect C001 `HostAdapter` and `KnowledgeBackend` interfaces in `src/expertiseos/hosts/contract.py` and `src/expertiseos/knowledge/backend.py`; reconcile the operation-key, expected-version, and exact-read-back requirements from `specs/002-consent-core/contracts/consent-api.md` before implementation (FR-010, FR-012, FR-014)
- [ ] T003 Inspect and minimally extend C001 test doubles in `tests/fakes.py` only through the reconciled contract so they can count mutation calls, preserve operation-key results, expose versions, and inject failures without storing unapproved candidates (FR-010, FR-012, SC-004)

**Checkpoint**: C001 contracts can express guarded mutation, exact read-back, version conflict, and idempotent retry without a bypass.

---

## Phase 2: Foundational Domain and State Primitives

**Purpose**: Establish shared types, validation, errors, and receipt storage required by every story.

- [ ] T004 [P] Add focused domain validation coverage for all enums, required explicit constructor fields, blank content, subject cardinality, versions, timestamps, relationship IDs/types, and retired-versus-deleted semantics in `tests/unit/test_domain_models.py` (FR-001, FR-002, FR-017, FR-024)
- [ ] T005 [P] Add SQLite receipt-store coverage for schema initialization, canonical object references, idempotent exact insert, divergent-operation-ID conflict, and absence of candidate/prompt content in `tests/unit/test_approval_receipts.py` (FR-013, FR-021)
- [ ] T006 [P] Define typed validation, lifecycle, approval, conflict, backend, read-back, receipt, and reconciliation errors in `src/expertiseos/domain/errors.py` (FR-003, FR-009, FR-022)
- [ ] T007 Implement the minimal enums and explicit-field records from `specs/002-consent-core/data-model.md` in `src/expertiseos/domain/models.py`, using C001's single model library and no dataclass definition defaults (FR-001, FR-002, FR-017, FR-023, FR-024)
- [ ] T008 Implement forward-only transactional initialization plus exact insert/get receipt operations in `src/expertiseos/state/sqlite.py`, creating only `approval_receipts` and rejecting divergent reuse without storing semantic payloads (FR-013, FR-021)
- [ ] T009 Run `tests/unit/test_domain_models.py` and `tests/unit/test_approval_receipts.py`, then run mypy on `src/expertiseos/domain/` and `src/expertiseos/state/sqlite.py`; preserve the commands and results for component evidence (SC-005, SC-008)

**Checkpoint**: All shared records validate deterministically, every field is explicit, and durable consent state contains only minimal completed receipts.

---

## Phase 3: User Story 1 - Save Exactly What Was Approved (Priority: P1)

**Goal**: Commit one exact displayed proposal only after one actual-user decision and produce one matching receipt.

**Independent Test**: Pass a real proposal and grant through the approval gate and guarded service into the conforming fake backend and temporary SQLite store; compare the exact object/version and receipt to the approved payload.

### Verification

- [ ] T010 [P] [US1] Add deterministic digest vectors covering key order, unordered categories/subjects/version maps, optional fields, exact content, shown provenance, relationship changes, and exclusion of runtime IDs/timestamps in `tests/unit/test_approval_gate.py` (FR-008)
- [ ] T011 [P] [US1] Add exact create/edit/direct-save/read-back/receipt and save-without-learning scenarios in `tests/unit/test_exact_write.py` (FR-010, FR-013, FR-019, FR-020, FR-023; SC-001)
- [ ] T012 [US1] Add the full producer-to-consumer consent scenario with real candidate/grant/gate/service, C001 fake backend, and temporary SQLite receipt store in `tests/integration/test_consent_commit_flow.py` (FR-006 through FR-014; SC-001, SC-008)

### Implementation

- [ ] T013 [US1] Implement canonical semantic-document construction and SHA-256 digest plus the in-memory `DecisionGrantStore` in `src/expertiseos/approval/gate.py` (FR-006 through FR-008)
- [ ] T014 [US1] Implement approval validation and successful grant-consumption semantics in `src/expertiseos/approval/gate.py`, keeping grants reusable only for bounded retry until complete success (FR-007, FR-009, FR-010)
- [ ] T015 [US1] Implement create, edit re-proposal, narrow direct-save proposal creation, decline, commit, and approved read coordination in `src/expertiseos/knowledge/service.py`; expose no direct host-facing backend mutation (FR-010, FR-014, FR-019, FR-020, FR-023)
- [ ] T016 [US1] Run the US1 unit and integration tests plus mypy on `src/expertiseos/approval/gate.py` and `src/expertiseos/knowledge/service.py`; verify success is returned only after exact read-back, receipt, grant consumption, and candidate approval (SC-001, SC-008)

**Checkpoint**: One exact approved create commits end to end, direct save remains narrow, and save alone does not advance learner state.

---

## Phase 4: User Story 2 - Reject Missing, Forged, or Stale Approval (Priority: P1)

**Goal**: Make every non-matching or non-user authorization path fail without mutation or receipt.

**Independent Test**: Submit each adversarial grant/event/version case to a real gate/service with mutation-counting fakes and verify zero writes and zero receipts.

### Verification

- [ ] T017 [P] [US2] Add missing grant, boolean/model claim, assistant text, tool-result Save, quoted old Save, unrelated yes, stale proposal, consumed grant, and modified-content cases in `tests/unit/test_stale_approval.py` (FR-006 through FR-011; SC-002)
- [ ] T018 [P] [US2] Add proposal-A-on-B, cross-session, and cross-adapter/Codex-to-Claude authorization cases in `tests/unit/test_cross_session_approval.py` (FR-006, FR-007, FR-009; SC-002)
- [ ] T019 [P] [US2] Add current-version mismatch, old approval after version change, and two-contender conflict cases with mutation-call assertions in `tests/unit/test_version_conflict.py` (FR-009, FR-016; SC-006)

### Implementation

- [ ] T020 [US2] Complete ordered gate checks and typed rejection/conflict results in `src/expertiseos/approval/gate.py`, ensuring no backend call occurs for an invalid proposal or grant (FR-007, FR-009, FR-011)
- [ ] T021 [US2] Enforce expected-version verification and truthful rejection/conflict/failure results in `src/expertiseos/knowledge/service.py` without automatic rebase, last-write-wins, or success fallback (FR-011, FR-016, FR-022)
- [ ] T022 [US2] Run all US2 adversarial tests and the integration commit flow; inspect fake mutation counts and temporary receipt rows to prove every negative case leaves both at zero (SC-002, SC-006)

**Checkpoint**: Model intent, ambiguous text, stale state, replay, and cross-host/session grants cannot authorize writes.

---

## Phase 5: User Story 3 - Decline or Leave Without Persistent Traces (Priority: P1)

**Goal**: Keep every unapproved proposal payload and decline suppression volatile across all terminal and restart paths.

**Independent Test**: Use unique marker content, exercise skip/cancel/unrelated-message/session-end/restart, and scan the component's fake backend and SQLite state for absence.

### Verification

- [ ] T023 [P] [US3] Add every legal transition, every illegal transition class, terminal-state immutability, lookup ownership, and session expiry case in `tests/unit/test_candidate_lifecycle.py` (FR-003, FR-005; SC-005)
- [ ] T024 [P] [US3] Add Skip, cancel, ignore/unrelated message, session end, fresh-store restart, late approval, and same-session-only suppression cases using unique markers in `tests/unit/test_decline_no_persistence.py` (FR-004, FR-005; SC-003)

### Implementation

- [ ] T025 [US3] Implement the explicit in-memory state machine, proposal/session indexes, terminal-state checks, expiry operations, and same-session decline fingerprints without a durable serializer in `src/expertiseos/domain/candidate_store.py` (FR-003 through FR-005)
- [ ] T026 [US3] Integrate decline and expiry with grant invalidation in `src/expertiseos/approval/gate.py` and guarded service behavior in `src/expertiseos/knowledge/service.py` (FR-005, FR-007, FR-014)
- [ ] T027 [US3] Run US3 tests, restart stores, and inspect the fake backend and temporary SQLite database to prove the marker is absent and late decisions fail (SC-003, SC-005)

**Checkpoint**: Unapproved content is unrecoverable by design, and session-local suppression cannot become a durable profile.

---

## Phase 6: User Story 4 - Safely Reconcile Interrupted Writes (Priority: P2)

**Goal**: Preserve truthful results and exactly-once semantic effects across backend, read-back, and receipt interruptions.

**Independent Test**: Inject failure at each commit boundary, retry with the same operation key, and assert one mutation result, one object/version, and one exact receipt.

### Verification

- [ ] T028 [P] [US4] Add backend-before-write failure, backend-after-write timeout, exact read-back mismatch, receipt-write failure, same-key retry, divergent-key reuse, and post-success retry cases in `tests/unit/test_exact_write.py` (FR-010 through FR-013, FR-022; SC-004)
- [ ] T029 [US4] Extend the integration flow in `tests/integration/test_consent_commit_flow.py` to fail SQLite receipt insertion after canonical success and reconcile through the actual operation-key contract without duplicate mutation (FR-012, FR-013; SC-004)

### Implementation

- [ ] T030 [US4] Implement bounded commit/reconciliation state handling and exact backend read-back comparison in `src/expertiseos/knowledge/service.py`, returning `incomplete` rather than Saved when receipt completion fails (FR-010 through FR-012, FR-022)
- [ ] T031 [US4] Implement receipt insert-or-read-exact reconciliation and integrity conflict behavior in `src/expertiseos/state/sqlite.py` without an operation journal unless a demonstrated failing case requires it (FR-012, FR-013, FR-021)
- [ ] T032 [US4] Run US4 unit/integration tests and inspect backend call counts, committed versions, receipts, grant state, and candidate state for every injected boundary (SC-004, SC-008)

**Checkpoint**: Partial failure never yields false success, and exact retries cannot duplicate a semantic write.

---

## Phase 7: User Story 5 - Versioned Semantic Changes and Inspectable Disagreement (Priority: P2)

**Goal**: Apply approved revisions, relationships, and retirement while preserving identity, lineage, provenance, and unresolved contradictions.

**Independent Test**: Approve each operation against current fake-backend versions, assert version increments and stable IDs, then prove stale or unapproved changes do not alter the stored graph.

### Verification

- [ ] T033 [P] [US5] Add revision version increment, stable identity, retirement-not-deletion, categorization, and grouped split/merge binding cases in `tests/unit/test_version_conflict.py` (FR-015, FR-016; SC-007)
- [ ] T034 [P] [US5] Add relation add/remove/change approval, unsupported-type validation, source/target expected versions, coexistence of contradictions, and no silent consolidation cases in `tests/unit/test_relationship_approval.py` (FR-015, FR-017, FR-018; SC-007)
- [ ] T035 [P] [US5] Add exact approved excerpt/scope, contribution origin, source-unavailable preservation, and no replacement-evidence cases in `tests/unit/test_provenance.py` (FR-002, FR-020; SC-007)

### Implementation

- [ ] T036 [US5] Implement revision, relationship change, and retirement proposal/commit operations in `src/expertiseos/knowledge/service.py` using the same gate, operation key, read-back, and expected-version path as create (FR-015 through FR-018)
- [ ] T037 [US5] Implement grouped approval binding for categorization, split, merge, and conflict-resolution effects in `src/expertiseos/knowledge/service.py` using existing create/revision/relationship/retirement primitives, with no separate workflow engine or silent source-object changes (FR-015, FR-018)
- [ ] T038 [US5] Run US5 tests and the integration commit flow, then verify stable IDs, monotonic versions, approved provenance, relationship traceability, retired status, and contradiction coexistence (SC-006, SC-007)

**Checkpoint**: Later components receive one guarded semantic-mutation API with predictable version and conflict behavior.

---

## Phase 8: Component Verification and Handoff

**Purpose**: Prove the planned consent boundary and publish integration-ready evidence.

- [ ] T039 Run the complete component pytest selection for `tests/unit/test_domain_models.py`, `tests/unit/test_candidate_lifecycle.py`, `tests/unit/test_approval_gate.py`, `tests/unit/test_exact_write.py`, `tests/unit/test_decline_no_persistence.py`, `tests/unit/test_stale_approval.py`, `tests/unit/test_cross_session_approval.py`, `tests/unit/test_version_conflict.py`, `tests/unit/test_relationship_approval.py`, `tests/unit/test_provenance.py`, `tests/unit/test_approval_receipts.py`, and `tests/integration/test_consent_commit_flow.py`; record exact command and zero exit status (SC-008)
- [ ] T040 Run the repository full test command defined in `pyproject.toml` to detect regressions outside this component and record any failure with its owning component rather than silently changing behavior (SC-008)
- [ ] T041 Run mypy against `src/expertiseos/domain/models.py`, `src/expertiseos/domain/candidate_store.py`, `src/expertiseos/domain/errors.py`, `src/expertiseos/approval/gate.py`, `src/expertiseos/knowledge/service.py`, and `src/expertiseos/state/sqlite.py`, then run the static/lint checks defined by `pyproject.toml`; fix all errors within C002 ownership and record exact commands/results (FR-024, SC-008)
- [ ] T042 Validate every scenario and stop condition in `specs/002-consent-core/quickstart.md`, including persistent-marker absence and actual producer-to-consumer reconciliation (SC-001 through SC-008)
- [ ] T043 Reconcile downstream contracts: confirm C003 cannot bypass guarded writes, give C004 the receipt/migration extension boundary, give C005/C006 grant-registration rules, and give C007/C008 result/idempotency constraints using `specs/002-consent-core/contracts/consent-api.md` and `specs/002-consent-core/contracts/state-schema.md` (FR-014, FR-021, FR-022)
- [ ] T044 Update `docs/implementation-status.md` with implemented scope, tests/commands, external assumptions, known limitations, and intentionally excluded files; do not claim real Basic Memory or live-host coverage from C002 (SC-008)

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 upstream reconciliation
  -> Phase 2 foundations
  -> US1 exact approved save
     -> US2 adversarial rejection
     -> US3 volatile refusal/expiry
     -> US4 interrupted-write reconciliation
     -> US5 versioned semantic changes
  -> Phase 8 full verification and downstream handoff
```

- US2 and US3 can proceed independently after US1 establishes the gate/service path.
- US4 depends on US1 commit ordering and the reconciled backend operation-key contract.
- US5 depends on US1 and the foundational versioned records; it does not depend on US3.
- C003-C008 remain blocked from relying on C002 contracts until Phase 8 integration promotion.

### Parallel Opportunities

- Foundational domain and receipt tests touch separate files and may run in parallel before their implementations.
- Within each story, test files marked `[P]` are independent; production edits to `approval/gate.py` and `knowledge/service.py` remain serialized under the stable C002 owner.
- No task marked `[P]` concurrently edits `knowledge/service.py`, `state/sqlite.py`, or another component's owned shared file.

## Implementation Strategy

1. Reconcile C001 contracts before writing production code.
2. Build the explicit types and minimal receipt store.
3. Complete the smallest end-to-end slice: proposal -> actual-user grant -> gate -> fake backend -> exact read-back -> SQLite receipt.
4. Expand negative coverage before adding revision/relationship breadth.
5. Add idempotent reconciliation and remaining semantic operations using the same primitives.
6. Run component, repository, type, static, and quickstart verification before handoff.

## Task Summary

- Total tasks: 44
- Setup/foundational: 9
- US1: 7
- US2: 6
- US3: 5
- US4: 5
- US5: 6
- Verification/handoff: 6
- Suggested first deliverable: US1 after Phases 1-2, immediately followed by release-blocking US2 and US3 negative coverage
