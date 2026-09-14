# Feature Specification: Feasibility and Repository Bootstrap

**Intent**: Define the evidence and minimal shared contracts required before expertiseOS feature development starts.

**Feature Branch**: `001-feasibility-bootstrap`

**Created**: 2026-09-14

**Status**: Draft

**Input**: User description: "Initialize and develop the expertiseOS MVP from the approved agent plan without over-design or missing features."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prove Safe Host Integration (Priority: P1)

As an expertiseOS user, I need each claimed write-capable host integration to distinguish my actual input from model or tool output and defer prompts until a safe checkpoint, so ordinary work continues without unauthorized persistence or interruption.

**Why this priority**: A host that cannot observe trustworthy user decisions cannot safely authorize writes, and this uncertainty blocks every later consent feature.

**Independent Test**: For each pinned host, activate a proposal, attempt a model-originated write, observe rejection, submit a matching user decision through the supported host input path, and verify that exactly one matching grant can be registered without interrupting an in-flight atomic operation.

**Acceptance Scenarios**:

1. **Given** an active proposal and no actual user decision event, **When** model or tool output claims approval, **Then** the integration provides no authorization for a write.
2. **Given** an active proposal displayed at a safe checkpoint, **When** the user submits a matching decision through the supported host input path, **Then** the adapter can bind the decision to that proposal, host, session, action, content, and expected versions.
3. **Given** an atomic host operation in progress, **When** a candidate becomes ready, **Then** no learning prompt appears until the narrowest supported safe checkpoint.
4. **Given** expertiseOS service failure, **When** the host performs ordinary work, **Then** the host task continues and no false persistence success is reported.

---

### User Story 2 - Prove Local Knowledge Backend (Priority: P1)

As an expertiseOS user, I need approved knowledge to remain local, inspectable, retrievable, and deletable without another model service, so later features can depend on a viable local persistence boundary.

**Why this priority**: The canonical backend and its distribution obligations affect the whole implementation and must be proven before product code depends on it.

**Independent Test**: In a pinned local backend installation, create only explicitly approved fixture data, read it by stable identity, search it, preserve required metadata and relationships, delete it, rebuild its index, and repeat supported operations with expertiseOS network access disabled after setup.

**Acceptance Scenarios**:

1. **Given** approved fixture knowledge, **When** it is created through supported backend interfaces, **Then** its current and exact historical content, identity, metadata, provenance, version, status, and relationships can be read or deterministically reconstructed.
2. **Given** approved indexed knowledge, **When** local search and deletion are exercised, **Then** search returns bounded results and deletion removes the in-scope canonical and index entries.
3. **Given** completed local setup and blocked outbound access, **When** supported read, write, search, delete, and rebuild operations run, **Then** no remote expertiseOS memory or model service is required.
4. **Given** the selected backend packaging approach, **When** release obligations are reviewed, **Then** the dependency version, distribution method, obligations, allowed pilot scope, and any release blocker are explicit.

---

### User Story 3 - Start Development on Stable Minimal Contracts (Priority: P2)

As a feature developer, I need one installable package, repeatable verification commands, narrow host and backend contracts, and deterministic fakes, so downstream work can proceed independently without live-host or live-backend coupling.

**Why this priority**: Shared contracts and fakes unblock the later component branches once feasibility is demonstrated.

**Independent Test**: Install the package in a clean supported environment, run its static and test entrypoints, execute contract smoke tests using deterministic fakes, and verify downstream code can consume normalized host events and approved-data backend operations without importing vendor internals.

**Acceptance Scenarios**:

1. **Given** a clean supported development environment, **When** the documented install and verification commands run, **Then** the package imports and all bootstrap checks use one repeatable entrypoint set.
2. **Given** the host contract, **When** a fake host emits session, user, atomic-operation, checkpoint, and session-end events, **Then** consumers receive normalized host-neutral events and truthful capability information.
3. **Given** the backend contract, **When** a fake backend exercises approved create, current and historical get, bounded search, update, relationship, retire, delete, rebuild, and health operations, **Then** it stores only approved test data and enforces stable identity, expected-version, and idempotent-command semantics.
4. **Given** an unavailable fake service or unsupported host capability, **When** a host fixture continues ordinary work, **Then** failure is explicit, writes remain unavailable, and the host work is not blocked.

### Edge Cases

- A host supports activation but exposes no trustworthy user-input event: report write capability as blocked/read-only.
- A host exposes no explicit atomic begin/end event: use the narrowest supported checkpoint and record the limitation without weakening authorization.
- A host exposes no stable session identifier: generate a local identifier that is scoped to and expires with that host session.
- Backend identities or relationships require a mapping: allow only the smallest documented sidecar mapping needed for the P0 contract.
- Canonical backend write succeeds while indexing fails: report canonical success and index health separately; never claim search readiness falsely.
- A semantic mutation retries with the same `operation_id` and identical command input: return the original result without another write; reuse of that `operation_id` with any different command input returns a typed conflict.
- Network-disabled semantic indexing is unavailable: prove bounded keyword search and record the degraded capability.
- Existing host configuration is present during install or uninstall: preserve unrelated configuration and reverse only expertiseOS registration.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feasibility gate MUST record exact tested versions or commits, operating-system scope, supported activation path, capabilities, status, and limitations for Codex, Claude Code, Python, the host integration dependency, Basic Memory, and any local indexing dependency used.
- **FR-002**: Each host feasibility proof MUST distinguish actual user-submitted input from assistant output, tool output, model arguments, and quoted prior text.
- **FR-003**: Each claimed write-capable host MUST support binding one actual user decision to one active proposal, adapter, session, action, displayed content digest, user-event reference, and relevant expected versions.
- **FR-004**: Each host proof MUST identify supported activation, configuration-preserving setup, reversible uninstall, safe checkpoint, atomic-operation boundary, normal handoff, and session-end behavior.
- **FR-005**: If FR-002 or FR-003 cannot be proven for a host, that host MUST be reported as read-only or blocked for writes; model compliance MUST NOT substitute for the missing boundary.
- **FR-006**: Ordinary host work MUST continue when expertiseOS service calls fail, while unverifiable writes fail closed and never report false success.
- **FR-007**: The backend feasibility proof MUST use supported public interfaces to exercise approved create, current-version read, exact historical-version read, bounded local search, required metadata/provenance/version/status, relationships, retire/delete, index rebuild, and health behavior.
- **FR-008**: The backend proof MUST demonstrate local operation after setup without a remote expertiseOS memory service or second generative-model API key, with a bounded keyword fallback when local semantic search is unavailable.
- **FR-009**: The feasibility result MUST record the exact Basic Memory version reviewed, packaging and startup method, applicable AGPL-3.0 obligations, allowed showcase or pilot distribution, and any public-release blocker.
- **FR-010**: The repository bootstrap MUST provide one installable `expertiseos` package, one local service development entrypoint, and repeatable unit, integration, end-to-end, static-type, lint, and format verification commands.
- **FR-011**: The shared host contract MUST expose only adapter identity, session identity, truthful capabilities, session lifecycle, actual user events, atomic-operation boundaries, safe checkpoints, and unambiguous decision registration as normalized host-neutral concepts.
- **FR-012**: The shared knowledge backend contract MUST expose only approved create, current or exact historical get with explicit retired-record inclusion, batched current-version lookup, bounded search, expected-version update, relationship change, retire, expected-version delete, index rebuild, and health operations needed by the MVP. Every semantic mutation MUST receive `operation_id` as its final, separate command argument; `operation_id` MUST NOT be approved semantic content. The same `operation_id` with identical command input MUST replay the original result, while reuse with different command input MUST return a typed idempotency conflict. Index rebuild is non-semantic maintenance outside this semantic idempotency contract.
- **FR-013**: Deterministic fakes MUST cover the shared host and backend contracts and MUST provide controllable time and identity generation only where tests require them.
- **FR-014**: The fake backend MUST store only data explicitly marked as approved test input, and bootstrap tests MUST prove that no model-only or missing user event authorizes a persistent write.
- **FR-015**: All external uncertainties and limitations MUST be recorded as reproducible evidence or explicit blockers; the gate MUST NOT silently change approval, privacy, local-only, or host-continuity behavior.
- **FR-016**: Bootstrap scope MUST exclude consent feature implementation, candidate lifecycle implementation, production Basic Memory mapping, learner state, export/restore, production host adapters, dashboards, cloud services, background workers, extra generative models, and generic workflow or policy frameworks.

### Key Entities

- **Host Capability Profile**: The tested host/version/OS combination, supported activation and lifecycle events, trustworthy user-input availability, session identity source, write capability, and known limitation.
- **Normalized Host Event**: A host-neutral session, actual-user-input, atomic-begin, atomic-end, checkpoint, or session-end signal with adapter/session identity and a host event reference where applicable.
- **Backend Capability Profile**: The tested backend/version/configuration and results for identity, approved-data mutation, metadata, relationship, retrieval, deletion, rebuild, health, offline, and degraded-mode operations.
- **Approved Knowledge Record Contract**: The minimal semantic content, identity, version, metadata, provenance, status, and relationship values accepted or returned by the backend boundary after authorization occurs elsewhere; runtime `operation_id` is not part of this content.
- **Compatibility Evidence**: Reproducible commands, fixtures, environment metadata, results, limitations, and release constraints for an external dependency or host.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every claimed write-capable host passes all six steps of the actual-user-decision fixture; a host missing any step is explicitly reported as read-only or blocked.
- **SC-002**: For both required hosts, the feasibility record covers 100% of activation, configuration preservation, uninstall, safe checkpoint, atomic boundary, user-input distinction, session identity, and service-failure questions.
- **SC-003**: The backend proof passes create/current-read/historical-read/search/delete/rebuild round trips and same-command replay/conflicting-command checks for approved fixtures with exact content and identity assertions and no use of private backend storage tables.
- **SC-004**: After setup, all supported local backend scenarios pass with outbound access blocked or the precise unsupported capability is recorded with a keyword fallback result.
- **SC-005**: The bootstrap verification suite includes and passes backend-contract, host-contract, no-write-without-user-event, and service-unavailable host-continuity checks.
- **SC-006**: A clean Python 3.12 environment can install the package, import it, and run the documented test and static-check commands without manual database or remote model-provider setup.
- **SC-007**: All required compatibility and license fields are populated with evidence; no claimed support status relies on an undocumented assumption.
- **SC-008**: Downstream components can run deterministic host and backend contract tests without a live Codex session, live Claude Code session, network access, or production Basic Memory store.

## Assumptions

- The approved MVP plan and constitution are authoritative for product semantics and scope.
- G0 determines exact supported external versions and mechanisms through executable or reproducible verification; planning does not pre-claim support.
- Python 3.12, one local process, one installable package, pytest, and a narrow loopback or local IPC transport are the default unless a verified incompatibility is recorded.
- Shared release and status documents are integration-owned; this component supplies the required evidence and content for integration rather than concurrently editing those files.
- Temporary feasibility spikes may exist during implementation but are removed before G0 closes unless retained as focused automated fixtures.

## Out of Scope

- Product-level consent, candidate, persistence, learning, control, retrieval, export, reliability, and production host-adapter behavior beyond the feasibility proofs and shared interfaces named above.
- Any cloud synchronization, remote memory service, extra generative model, public listener, dashboard, background process, generic workflow engine, policy DSL, event-sourcing system, or speculative compatibility layer.
