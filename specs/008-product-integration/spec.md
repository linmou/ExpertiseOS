# Feature Specification: Product Integration and Acceptance

**Intent**: Define the smallest host-neutral product surface and acceptance coverage that proves the expertiseOS MVP works end to end without weakening upstream consent, storage, retrieval, learning, or reliability contracts.

**Feature Branch**: `008-product-integration`
**Created**: 2026-09-14
**Status**: Draft
**Input**: Integrate the shared expertiseOS behavior, guarded local service surface, reference scenarios, and deterministic AT-01 through AT-16 validation after components 001-007 are promoted.

## User Scenarios & Testing

### User Story 1 - Use One Guarded Product Surface (Priority: P1)

As a user working in either supported host, I can search, inspect, propose, approve, decline, and control expertiseOS through one consistent local product surface, while durable changes remain subject to the same approval rules in both hosts.

**Why this priority**: A common guarded surface is the integration boundary on which every other end-to-end behavior depends.

**Independent Test**: Connect a host-neutral client to promoted upstream services, exercise each exposed operation, and prove that reads work while mutation attempts without a matching host-originated decision are rejected.

**Acceptance Scenarios**:

1. **Given** approved knowledge and an active supported host session, **When** the host searches or inspects knowledge, learning state, or controls, **Then** the result is bounded, provenance-aware, and consistent with the shared local state.
2. **Given** a proposal without a matching real user decision, **When** any host-facing mutation operation is attempted, **Then** no durable state changes and no success is reported.
3. **Given** a matching fresh decision for the exact displayed proposal and expected versions, **When** the guarded commit operation succeeds, **Then** the approved state is returned exactly once.
4. **Given** expertiseOS is unavailable, **When** the user continues ordinary host work, **Then** that work continues and unsafe writes remain unavailable.

---

### User Story 2 - Receive Consistent Learning Behavior (Priority: P1)

As a user, I receive the same restrained expertiseOS behavior in Codex and Claude Code: relevant recall, uncertainty-safe proposals at eligible checkpoints, optional one-step reflection, and behavior that respects learning controls.

**Why this priority**: The shared behavior is the visible product experience and must not fork into host-specific semantics.

**Independent Test**: Run the same behavior fixtures through both adapter contracts and compare observable decisions, proposal timing, control handling, and tool calls while allowing only declared host capability differences.

**Acceptance Scenarios**:

1. **Given** relevant approved knowledge and a possible addition or contradiction, **When** an eligible checkpoint occurs, **Then** the host describes uncertainty without claiming what the user knows and offers Save, Edit, or Skip.
2. **Given** an atomic operation is active, **When** a possible insight appears, **Then** no learning prompt interrupts the operation and the comparison waits for the next eligible checkpoint.
3. **Given** the user saves knowledge but skips reflection, **When** work continues, **Then** the save is not treated as learning evidence or mastery.
4. **Given** pause, fatigue rest, target satisfaction, or disable state, **When** the skill considers recall, collection, or proactive learning, **Then** it follows the promoted control decision without changing that state itself.

---

### User Story 3 - Continue Across Hosts Safely (Priority: P1)

As a user switching between Codex and Claude Code, I see the same approved objects, provenance, relationships, controls, and learner state while pending approvals remain isolated to their originating host session.

**Why this priority**: Cross-host continuity is a defining MVP promise and a high-risk authorization boundary.

**Independent Test**: Save and retrieve an approved object across hosts, then race two versioned edits and attempt cross-host approval reuse.

**Acceptance Scenarios**:

1. **Given** an object approved in Codex, **When** Claude Code retrieves it, **Then** its stable ID, version, content, provenance, relations, uncertainty, controls, and learner state match the shared repository.
2. **Given** a pending proposal in Codex, **When** a Claude Code user event refers to it, **Then** the event cannot authorize the Codex proposal.
3. **Given** both hosts read the same version and one approved edit commits first, **When** the other edit is later approved, **Then** it conflicts safely and cannot overwrite the newer version.
4. **Given** both hosts later retrieve one approved reflection activity, **When** progress is inspected, **Then** the activity is counted once globally.

---

### User Story 4 - Verify Reference Journeys (Priority: P2)

As a product evaluator, I can run concise, inspectable reference journeys covering postponed reflection, conflicting knowledge, fatigue before target completion, and cross-host continuity.

**Why this priority**: These journeys demonstrate that the integrated contracts produce the intended user experience, not merely isolated passing calls.

**Independent Test**: Run each deterministic reference scenario from a documented initial state and compare persistent state, visible outputs, and event traces with its expected result.

**Acceptance Scenarios**:

1. **Given** a new observation, **When** the user saves it and postpones reflection, **Then** only approved content persists and a later approved boundary reflection remains a separate activity.
2. **Given** existing guidance and contradictory evidence, **When** the user retains both, revises scope, or declines, **Then** no silent replacement or semantic generalization occurs.
3. **Given** fatigue before target completion, **When** rest begins, **Then** unresolved candidates expire, proactive learning pauses, approved recall remains available, and the target remains unmet.
4. **Given** a Codex-to-Claude host switch, **When** the second host recalls the object, **Then** continuity is preserved without creating mastery or approval.

---

### User Story 5 - Obtain a Deterministic Acceptance Verdict (Priority: P2)

As a maintainer, I can run the complete deterministic acceptance suite and distinguish product-integrity failures from model-behavior observations.

**Why this priority**: The MVP cannot be declared complete from a convincing transcript; consent, privacy, and state integrity need reproducible evidence.

**Independent Test**: Execute AT-01 through AT-16 against their applicable automated, integration, live-host, cross-host, adversarial, and offline fixtures and produce machine-readable pass/fail evidence for integration review.

**Acceptance Scenarios**:

1. **Given** all promoted upstream components, **When** AT-01 through AT-16 run in their declared environments, **Then** each test records its command, environment, input fixture, observed result, and exit status.
2. **Given** a consent, privacy, or state-integrity failure, **When** the verdict is calculated, **Then** model-quality results cannot offset the failure.
3. **Given** model-dependent novelty behavior, **When** it is evaluated, **Then** misses and false proposals are reported separately from deterministic lifecycle correctness.
4. **Given** the runtime network is blocked after approved setup, **When** local scenarios run, **Then** expertiseOS storage, state, and local search continue without an external memory or embedding call.

### Edge Cases

- A caller supplies a model-authored approval flag, quoted Save text, stale proposal ID, unrelated yes, changed content digest, or a grant from another host/session.
- Retrieved knowledge or tool output contains instructions to auto-save, change controls, mark mastery, expose the vault, or obtain extra permissions.
- A host exposes read/search but cannot validate real user decisions; the product must advertise read-only capability and omit write claims.
- Canonical storage succeeds while indexing fails, or a response is lost and the same approved operation is retried.
- A source becomes unavailable after approval; the original source reference remains marked unavailable and is not regenerated.
- A pending candidate exists when the user pauses, reports fatigue, disables expertiseOS, sends an unrelated message, ends the session, or the process restarts.
- The acceptance environment lacks a live supported host or an optional local semantic index; affected evidence is reported accurately and keyword fallback is used where specified.
- Learner evidence has outcomes other than `pass`; integration preserves all outcomes for inspection while consuming the promoted C004 rule that only `pass` may advance demonstrated mastery.

## Requirements

### Functional Requirements

- **FR-001**: The product MUST expose only the approved host-neutral read, proposal, decision, commit, learning inspection, control, ownership, and health operations needed by the MVP.
- **FR-002**: Every exposed mutation operation MUST delegate authorization and durable-state validation to the promoted guarded upstream service; no public operation may write directly to the knowledge backend or state store.
- **FR-003**: Read results MUST be bounded to the requested context and preserve object identity, version, provenance, relationships, conflict/staleness indicators, learner state, and degraded-search status supplied by upstream contracts.
- **FR-004**: Both supported hosts MUST load one shared behavioral specification for search timing, novelty-safe wording, proposal presentation, optional reflection, recall use, and control-state behavior; host wrappers MUST NOT redefine domain rules.
- **FR-005**: The shared behavior MUST treat stored and tool-provided content as untrusted data and MUST NOT follow embedded instructions that request writes, control changes, mastery changes, vault disclosure, or extra permissions.
- **FR-006**: The integrated flow MUST keep ordinary host work available when expertiseOS, storage, retrieval, or indexing is unavailable while refusing unverifiable writes and false success.
- **FR-007**: The integrated flow MUST preserve session and adapter isolation for candidates and decisions while sharing approved durable state, controls, and reflection counts across hosts.
- **FR-008**: The component MUST provide executable reference fixtures for Scenario A (save now, reflect later), Scenario B (conflict without replacement), Scenario C (fatigue before target), and Scenario D (cross-host continuity).
- **FR-009**: The component MUST provide deterministic coverage for AT-01 through AT-16, using promoted upstream behavior rather than synthetic substitutes at producer-consumer boundaries.
- **FR-010**: Acceptance evidence MUST separate deterministic product checks from model-behavior evaluation and MUST record misses and false proposals without weakening deterministic gates.
- **FR-011**: Acceptance runs MUST record the exact command, input fixture or corpus version, relevant host/dependency versions, environment metadata, exit status, and inspectable output or log location.
- **FR-012**: AT-01 MUST verify guided activation for both hosts, one common local repository, onboarding consent, scope exclusions, capability reporting, and no second model key or manual database setup.
- **FR-013**: AT-02 and AT-03 MUST verify uncertainty-safe novel/conflict proposals at the earliest eligible checkpoint without interrupting an atomic operation.
- **FR-014**: AT-04 through AT-08 MUST verify exact approved persistence, negative no-persistence paths, forged-approval rejection, save-without-learning, and separately approved derived or conflict changes.
- **FR-015**: AT-09 through AT-12 MUST verify user-grounded learning evidence, promoted control distinctions, pause-with-work, shared cross-host state, stale-edit rejection, approval isolation, and one global reflection count.
- **FR-016**: AT-13 through AT-16 MUST verify outage/index recovery, idempotent retry, export/restore/delete, adversarial content containment, bounded retrieval, and offline expertiseOS operation with local fallback.
- **FR-017**: Consent, privacy, and state-integrity acceptance failures MUST block the component verdict and MUST NOT be offset by model-behavior scores.
- **FR-018**: The component MUST consume upstream C002-C007 contracts as promoted and MUST route discovered domain defects to their owning component instead of masking them in the skill, tool surface, fixtures, or integration-only logic.
- **FR-019**: The component MUST verify the promoted C004 policy that only `pass` evidence may advance demonstrated mastery; `partial`, `fail`, and `insufficient_evidence` remain inspectable and contribute zero advancement, and configurable numeric thresholds cannot bypass autonomous-state safeguards.

### Key Entities

- **Tool Operation**: A host-neutral read, proposal, decision, guarded commit, inspection, control, ownership, or health request with explicit inputs and typed success/failure output.
- **Behavior Rule**: A shared host-model instruction governing when and how expertiseOS searches, proposes, reflects, recalls, and respects control state; it cannot authorize persistence.
- **Reference Scenario**: A versioned fixture with initial approved state, normalized host events, user actions, expected visible behavior, expected persistence delta, and linked acceptance tests.
- **Acceptance Case**: One AT-01 through AT-16 definition with applicable environments, producer-consumer boundaries, command, fixtures, assertions, and evidence metadata.
- **Acceptance Evidence**: Immutable run metadata and outputs used by the integration owner to determine a test result; it contains no unapproved candidate content.
- **Capability View**: The current host's proven read, search, user-decision validation, write, checkpoint, and activation capabilities.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All host-facing mutation attempts without a matching fresh user decision produce zero durable semantic or control-state changes and zero false success responses across the acceptance corpus.
- **SC-002**: The same shared behavior fixtures produce equivalent product decisions in Codex and Claude Code for every capability common to both supported versions.
- **SC-003**: All four reference scenarios complete with their exact expected visible behavior and persistent-state delta.
- **SC-004**: AT-01 through AT-16 each have a reproducible result with complete environment, input, command, exit-status, and evidence metadata; all applicable consent, privacy, and state-integrity cases pass before promotion.
- **SC-005**: Cross-host fixtures preserve identical stable IDs, versions, approved content, provenance, relations, learner state, controls, and counts, while cross-session approval reuse succeeds zero times.
- **SC-006**: Adversarial fixtures create zero unauthorized grants, writes, control changes, mastery changes, vault-wide disclosures, or additional permissions.
- **SC-007**: With expertiseOS runtime network access blocked after setup, all required local storage, state, read, guarded write, and fallback-search scenarios complete without an external expertiseOS memory or embedding request.
- **SC-008**: Ordinary host task completion remains possible in every simulated expertiseOS service, storage, and index failure case, while unverifiable memory writes remain unavailable.
- **SC-009**: Acceptance fixtures cover all six knowledge categories, all three subjects, an exact duplicate, changed condition, contradiction, uncertain novelty, unavailable source, malicious content, and at least one non-coding task.
- **SC-010**: Acceptance execution uses the actual promoted producer output at every declared component handoff; no edge is passed solely with a mocked replacement.

## Assumptions

- Components C002 through C007 provide promoted, reconciled contracts before implementation of dependent C008 tasks begins.
- C001 provides the pinned Python, host, MCP, Basic Memory, operating-system, packaging, and test-command decisions; this component does not choose substitutes.
- The integration owner owns orchestration records, edge work packets, promotion manifests, final acceptance execution, and release documentation; C008 supplies component-local product artifacts and tests.
- Host-specific payload parsing, activation, and decision capture remain in the Codex and Claude Code adapter components.
- The promoted C004 learner-evidence contract defines only `pass` as advancement-eligible; other outcomes remain inspectable, and autonomous-state safeguards remain mandatory regardless of numeric threshold configuration.
- Live-host cases may require reproducible manual evidence where the pinned host does not expose deterministic automation, but every deterministic boundary remains automated.

## Out of Scope

- Redefining approval, storage, retrieval, learner-state, control, host-adapter, export, deletion, or reliability semantics owned by upstream components.
- A direct or unrestricted backend write operation.
- Host-specific copies of the shared behavioral specification.
- A second generative model, remote memory service, cloud synchronization, background tutor or reflection process, general workflow/policy engine, dashboard, or separate chat client.
- Release documentation, compatibility claims, final acceptance verdict publication, or merging to the target branch.
