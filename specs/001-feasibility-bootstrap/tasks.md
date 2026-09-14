# Tasks: Feasibility and Repository Bootstrap

**Intent**: Provide dependency-ordered implementation and verification work for G0 without expanding into product features.

**Input**: Design documents from `/specs/001-feasibility-bootstrap/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

## Format

Each task follows `[ID] [P?] [Story?] Description with exact file path` and cites covered requirements.

## Phase 1: Setup

**Purpose**: Create the smallest installable and verifiable package skeleton.

- [X] T001 Create Python 3.12 package metadata and stable format, lint, mypy, import, unit, and integration command definitions in `pyproject.toml` (FR-010)
- [X] T002 Create package markers in `src/expertiseos/__init__.py`, `src/expertiseos/hosts/__init__.py`, and `src/expertiseos/knowledge/__init__.py` (FR-010)
- [X] T003 Create a non-networked local development process entrypoint stub that isolates expertiseOS failure from caller work in `src/expertiseos/__main__.py` (FR-006, FR-010)
- [X] T004 [P] Create unit/integration/e2e test directories and shared pytest configuration in `tests/conftest.py` (FR-010)
- [X] T005 [P] Create a version/environment evidence schema and evidence output directory description in `specs/001-feasibility-bootstrap/evidence/README.md` (FR-001, FR-015)

**Checkpoint**: Package imports and all verification command entrypoints resolve without product behavior.

---

## Phase 2: Foundational Contracts

**Purpose**: Freeze shared protocols and deterministic fixtures before external proofs.

- [X] T006 Implement required-field normalized host capability, event, session, decision-binding, and observation values plus the `HostAdapter` protocol in `src/expertiseos/hosts/contract.py` (FR-011)
- [X] T007 Implement validation for lifecycle ordering, event-origin distinction, session scope, atomic checkpoint eligibility, and evidence-backed capability claims in `src/expertiseos/hosts/contract.py` (FR-002, FR-004, FR-011)
- [X] T008 Implement required-field approved semantic knowledge, record, relation, search, health, and delete/rebuild result values plus the canonical `KnowledgeBackend` signatures with `operation_id` last on create/update/relationships/retire/delete, version-aware get with explicit retired inclusion, batched current-version lookup, and expected-version delete in `src/expertiseos/knowledge/backend.py` (FR-007, FR-012)
- [X] T009 Implement bounded-query, stable-identity, exact historical/default-current lookup, retired-record filtering, batched current-version mapping, expected-version mutation checks, same-command replay, reused-`operation_id` divergent-input conflict, and canonical/index health validation in `src/expertiseos/knowledge/backend.py` (FR-007, FR-012)
- [X] T010 Implement deterministic clock/ID helpers, `FakeHostAdapter`, and approved-input-only `FakeKnowledgeBackend` in `tests/fakes.py` (FR-013, FR-014)
- [X] T011 [P] Add host protocol unit checks for lifecycle, origin distinction, exact decision binding, checkpoint eligibility, missing evidence, and constructor-required fields in `tests/unit/test_host_contract.py` (FR-002, FR-003, FR-004, FR-011, FR-013)
- [X] T012 [P] Add backend protocol unit checks for approved create/default-current-get/exact-historical-get, retired inclusion, batched current versions, bounds, stable identity, expected-version conflicts including delete, relationships, retire/delete/rebuild, health separation, same-`operation_id`/same-input replay and same-`operation_id`/different-input conflict on every semantic mutation, new-`operation_id` command behavior, unapproved input rejection, and constructor-required fields in `tests/unit/test_backend_contract.py` (FR-007, FR-012, FR-013, FR-014)

**Checkpoint**: Downstream components can execute deterministic contract suites without live hosts, network, or Basic Memory.

---

## Phase 3: User Story 1 - Prove Safe Host Integration (Priority: P1)

**Goal**: Establish evidence-backed activation, actual-user decision, safe-checkpoint, session, and failure-continuity capabilities for each host.

**Independent Test**: Run the pinned-host fixture from proposal through rejected model write, actual user decision, exact one-use observation, and service failure while preserving the host task.

- [X] T013 [P] [US1] Define concise adversarial event fixtures distinguishing user, assistant, tool, model-argument, quoted, unrelated, stale, cross-session, and cross-host inputs in `tests/fixtures/host_events.json` (FR-002, FR-003)
- [X] T014 [P] [US1] Create the evidence recorder/checker for exact component/version/OS/capability/steps/fixture/result/exit-status/timestamp/limitation metadata in `tests/feasibility/evidence.py` (FR-001, FR-015)
- [X] T015 [US1] Build the reusable six-step actual-user-decision contract fixture for both hosts in `tests/integration/test_host_feasibility.py` (FR-002, FR-003, FR-005)
- [X] T016 [P] [US1] Add no-write-without-actual-user-event integration coverage for every adversarial event kind in `tests/integration/test_no_write_without_user_event.py` (FR-002, FR-005, FR-014)
- [X] T017 [P] [US1] Add a service-unavailable host fixture proving ordinary task completion and closed/accurate write status in `tests/integration/test_service_failure_continuity.py` (FR-006)
- [X] T018 [US1] Execute and record pinned Codex activation, configuration preservation, uninstall, lifecycle/checkpoint, user-input, session identity, and failure-continuity evidence under `specs/001-feasibility-bootstrap/evidence/codex/` (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006)
- [X] T019 [US1] Execute and record pinned Claude Code activation, configuration preservation, uninstall, lifecycle/checkpoint, user-input, session identity, and failure-continuity evidence under `specs/001-feasibility-bootstrap/evidence/claude-code/` (FR-001, FR-002, FR-003, FR-004, FR-005, FR-006)
- [X] T020 [US1] Classify each host capability from passed evidence, marking missing decision binding read-only/blocked, in `specs/001-feasibility-bootstrap/evidence/host-capability-matrix.md` (FR-001, FR-005, FR-015)

**Checkpoint**: Every host support claim is evidence-backed; missing authorization cannot be reported as write-capable.

---

## Phase 4: User Story 2 - Prove Local Knowledge Backend (Priority: P1)

**Goal**: Establish supported local approved-data operations and license constraints for Basic Memory.

**Independent Test**: Run approved create/current-read/historical-read/search/metadata/relation/delete/rebuild/health round trips and mutation replay/conflict checks on the pinned backend, then repeat supported scenarios with outbound access blocked.

- [X] T021 [P] [US2] Define compact approved-only backend fixtures covering metadata, provenance, versions, status, relationships, keyword matches, and deletion in `tests/fixtures/approved_knowledge.json` (FR-007)
- [X] T022 [US2] Build public-interface Basic Memory create/current-read/exact-historical-read/search/metadata/relation/delete/rebuild/health and same-command replay/divergent-input conflict feasibility checks in `tests/integration/test_backend_feasibility.py` (FR-007, FR-012)
- [X] T023 [US2] Add an outbound-blocked post-setup fixture with explicit semantic/keyword mode assertions in `tests/integration/test_local_backend_offline.py` (FR-008)
- [X] T024 [US2] Execute and record the pinned Basic Memory version, OS, public-interface current/historical round trips, identity mapping, metadata/relations, mutation replay/conflict, delete/rebuild, and health results under `specs/001-feasibility-bootstrap/evidence/basic-memory/` (FR-001, FR-007, FR-012, FR-015)
- [X] T025 [US2] Execute and record network-disabled local operation and keyword fallback evidence under `specs/001-feasibility-bootstrap/evidence/offline/` (FR-008, FR-015)
- [X] T026 [US2] Record the reviewed Basic Memory version, startup/distribution approach, AGPL-3.0 obligations, pilot status, and release blocker in `specs/001-feasibility-bootstrap/evidence/basic-memory-license.md` (FR-009, FR-015)

**Checkpoint**: Canonical approved data round-trips locally through supported interfaces and release constraints are explicit.

---

## Phase 5: User Story 3 - Start Development on Stable Minimal Contracts (Priority: P2)

**Goal**: Demonstrate that later components can consume package commands, contracts, and fakes independently.

**Independent Test**: In a clean environment, install/import the package and run static, contract, and integration checks without live hosts, network, or production Basic Memory.

- [X] T027 [US3] Add a downstream-consumer smoke test importing both protocols and exercising both deterministic fakes in `tests/integration/test_downstream_bootstrap.py` (FR-010, FR-011, FR-012, FR-013)
- [X] T028 [US3] Run format, Ruff, strict mypy, import, unit, and integration commands and record exact results in `specs/001-feasibility-bootstrap/evidence/bootstrap-verification.md` (FR-010, FR-015)
- [X] T029 [US3] Audit the component diff for excluded feature logic and prohibited infrastructure, recording results in `specs/001-feasibility-bootstrap/evidence/scope-audit.md` (FR-016)
- [X] T030 [US3] Produce integration-ready compatibility and implementation-status content with evidence links, without editing integration-owned shared docs, in `specs/001-feasibility-bootstrap/evidence/integration-handoff.md` (FR-001, FR-009, FR-015)

**Checkpoint**: Package, contracts, fakes, and evidence are ready for serial integration and downstream promotion.

---

## Phase 6: G0 Gate

- [ ] T031 Rerun all unchanged verification commands at the committed candidate SHA and record immutable command results in `specs/001-feasibility-bootstrap/evidence/g0-gate.md` (SC-003, SC-005, SC-006)
- [ ] T032 Evaluate host decision fixtures, capability completeness, backend/offline results, license status, scope audit, and static checks and record `PASS`, `PASS WITH DOCUMENTED COMPATIBILITY LIMIT`, or `BLOCKED` in `specs/001-feasibility-bootstrap/evidence/g0-verdict.md` (SC-001, SC-002, SC-004, SC-007, SC-008)

## Dependencies & Execution Order

- Setup precedes foundational contracts.
- T006-T010 precede their contract tests T011-T012.
- T011-T017 precede live host evidence T018-T020.
- T008-T012 and T021 precede backend proof T022-T026.
- Host and backend live evidence may run independently after foundational checks.
- T027-T030 require both contract suites; T031-T032 require every preceding task.

## Parallel Opportunities

- T004 and T005 can proceed after T001.
- Host and backend value/protocol files have separate owners, but T010 begins after their shapes stabilize.
- T011 and T012 are separate test files.
- T013 and T014 are independent fixtures.
- T016 and T017 are independent integration tests after T015's reusable fixture shape is stable.
- Codex and Claude live checks may run independently on isolated disposable configurations.
- Backend fixture preparation and host evidence work do not share paths.

## Implementation Strategy

1. Complete setup and deterministic contracts first.
2. Prove host and backend boundaries independently.
3. Add only the package wiring needed by downstream consumers.
4. Run static, integration, scope, offline, and evidence-completeness gates.
5. Stop with an explicit blocker rather than weakening semantics.

## Notes

- Test tasks are required because G0 is an executable feasibility gate.
- Live/manual evidence is acceptable only when automation is unavailable and exact steps/environment/results are recorded.
- New Python test/code files must begin with the required interpreter directive and purpose comment under repository instructions.
- No task edits integration-owned `README.md`, `docs/compatibility.md`, or `docs/implementation-status.md`.
