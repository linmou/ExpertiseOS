# Feature Specification: Codex Host Adapter

**Feature Branch**: `005-codex-host`
**Created**: 2026-09-14
**Status**: Draft
**Input**: User description: "Build the supported Codex onboarding and host adapter from the expertiseOS MVP plan, preserving exact user authorization, safe checkpoints, shared local state, accurate capability reporting, and ordinary Codex work during expertiseOS failures."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Onboard a Supported Codex Host (Priority: P1)

A user consents to expertiseOS during guided setup, after which supported Codex sessions activate the integration automatically and connect to the shared local expertiseOS service without disturbing unrelated Codex configuration.

**Why this priority**: No host behavior is valid until support, consent, activation, and service boundaries are established accurately.

**Independent Test**: In a fresh pinned Codex environment, complete onboarding, open a new session, and verify activation, service health, bounded control-state loading, reversible registration, and accurate capabilities without a second model key or manual storage setup.

**Acceptance Scenarios**:

1. **Given** a supported Codex installation and no expertiseOS consent, **When** guided onboarding completes with consent, **Then** a fresh Codex session automatically activates the shared local integration without overwriting unrelated host configuration.
2. **Given** an unverified or unsupported Codex version or permission mode, **When** setup evaluates it, **Then** the user sees the unsupported capabilities and knowledge writes remain unavailable.
3. **Given** a completed installation, **When** the user uninstalls the Codex integration, **Then** expertiseOS registration is reversed while unrelated Codex configuration and the separately chosen local data remain intact.

---

### User Story 2 - Work Without Unsafe Interruption (Priority: P1)

A user completes ordinary Codex work while expertiseOS observes only supported, in-scope host events and waits for a safe conversational checkpoint before surfacing a memory or learning proposal.

**Why this priority**: The host owns the task; expertiseOS must neither interrupt an incomplete atomic operation nor make host work depend on its own availability.

**Independent Test**: Run a bounded multi-tool Codex operation with a candidate detected mid-operation, inject service/search failures, and verify that no expertiseOS prompt appears until the first verified safe checkpoint and that Codex still completes the task.

**Acceptance Scenarios**:

1. **Given** an atomic Codex operation is in progress, **When** an event makes comparison due, **Then** no expertiseOS proposal interrupts the operation and the proposal can appear only at the next supported safe checkpoint.
2. **Given** expertiseOS service or retrieval is unavailable, **When** Codex performs ordinary work, **Then** that work continues and no false successful memory operation is reported.
3. **Given** the current source, path, or session is excluded by user controls, **When** Codex emits host events in that scope, **Then** the adapter does not forward their content for candidate detection or contextual retrieval.

---

### User Story 3 - Authorize an Exact Proposal (Priority: P1)

A user responds Save, Edit, or Skip to one active proposal through Codex's verified actual-user input path, and only an unambiguous, current response can resolve that proposal.

**Why this priority**: Actual-user event binding is the security boundary that prevents model text, tool output, stale decisions, or another session from authorizing persistence.

**Independent Test**: Present one active proposal, exercise Save/Edit/Skip and adversarial non-user or ambiguous inputs, and verify that only a fresh matching actual-user event creates the expected one-use decision registration.

**Acceptance Scenarios**:

1. **Given** one active displayed proposal, **When** the user submits an unambiguous Save through the verified Codex user-input path, **Then** the adapter registers one decision for the same proposal, session, adapter, action, and displayed content digest.
2. **Given** an Edit response containing final content, **When** the adapter processes it, **Then** revised content is re-displayed with a new binding and requires a decision matching that revised digest before commit.
3. **Given** a clear Skip or cancel, **When** the adapter processes the actual user event, **Then** the active proposal is declined or expired without a write grant.
4. **Given** model output, tool output, quoted Save text, an unrelated response, an ambiguous response, or an event from another session, **When** it is processed, **Then** it does not create a decision grant; an unrelated actual user message expires the unresolved proposal.

---

### User Story 4 - Share Local State Without Sharing Authorization (Priority: P2)

A Codex session reads approved knowledge and controls from the same local expertiseOS service used by other supported hosts while its pending proposals and decisions remain isolated to its own session.

**Why this priority**: Shared approved state provides continuity, but proposal authorization must never cross host or session boundaries.

**Independent Test**: Retrieve an approved object through Codex, attempt to reuse another host/session's decision, and verify shared reads alongside rejection of cross-host, cross-session, and stale approval.

**Acceptance Scenarios**:

1. **Given** approved knowledge exists in the shared local service, **When** Codex requests it, **Then** Codex receives the same stable object ID, version, provenance, relations, learner state, and control state available to other supported hosts.
2. **Given** a proposal belongs to another host or Codex session, **When** a Codex user event attempts to resolve it, **Then** no matching decision is registered.
3. **Given** a Codex proposal references an older object version, **When** its decision reaches the guarded service after another client updates the object, **Then** the stale commit is rejected and Codex can surface the current version for a new proposal.

### Edge Cases

- A session ends with an active proposal: unresolved candidates and unused decision grants expire, and no candidate recovery content is persisted.
- Atomic begin/end events are nested or unbalanced: no checkpoint is declared safe until the adapter can prove the operation is outside all supported atomic boundaries.
- More than one proposal appears active: the adapter requires itemized disambiguation and grants none from a generic response.
- The user says "Edit" without final replacement content: the host may prepare and display a revision, but no decision is granted until a later clear actual-user response.
- A direct "save this" command lacks a deterministically identifiable payload: the adapter requests a displayed proposal instead of authorizing inferred content.
- The local service disconnects during proposal handling: ordinary Codex work continues, the write is not reported as saved, and host output does not become retry authorization.
- Capability discovery is incomplete: unknown capabilities are reported unavailable rather than assumed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Guided Codex onboarding MUST detect the supported installation surface, verify version and permission mode, explain observation/storage/host-model boundaries, obtain consent before registration, preserve unrelated host configuration, connect the shared local service, run a health check, and provide a reversible uninstall path.
- **FR-002**: Automatic activation MUST use only a released or otherwise G0-verified supported Codex integration mechanism on exact tested host versions and operating systems.
- **FR-003**: The adapter MUST expose capabilities individually for read, search, actual-user decision validation, write, atomic-boundary observation, and automatic activation; unverified capabilities MUST be false.
- **FR-004**: The adapter MUST normalize supported Codex payloads into host-neutral session-start, actual-user, atomic-start, atomic-finish, safe-checkpoint, and session-end events while keeping Codex-specific payload types inside the adapter.
- **FR-005**: Every adapter session MUST have a stable identifier scoped to the active Codex session; a generated expertiseOS identifier is acceptable only when G0 proves Codex exposes no suitable identifier and its lifetime is bound to that session.
- **FR-006**: The adapter MUST prevent expertiseOS-initiated proposal or learning prompts while any supported atomic operation is incomplete and MUST use the narrowest verified safe checkpoint when the host lacks a complete atomic event stream.
- **FR-007**: Low-level events MAY mark comparison due but MUST NOT trigger fresh semantic analysis after every event or introduce a scheduler; ordinary Codex task steps MUST continue while a proposal is unresolved.
- **FR-008**: Before forwarding host content for observation or retrieval, the adapter MUST apply upstream user controls and source/path/session exclusions; disabled mode MUST prevent expertiseOS observation and recall.
- **FR-009**: Only an event proven by G0 to originate from actual Codex user input MAY be considered for decision registration; assistant output, tool output, model arguments, generic tool permission, and quoted prior decisions MUST NOT authorize a write.
- **FR-010**: For one active proposal, an unambiguous user response MUST bind the action to the proposal ID, adapter ID, session ID, displayed content digest, user-event reference, and any expected object versions required by the upstream approval contract.
- **FR-011**: Save MUST register at most one matching one-use decision through the upstream approval interface; Skip or cancel MUST decline or expire the proposal without registering a write decision.
- **FR-012**: Edit with explicit final content MUST update and re-display the volatile proposal with a new digest; Edit without final content MUST wait for re-display and a later matching user decision.
- **FR-013**: An unrelated next actual-user message MUST expire the unresolved proposal; ambiguous responses and multiple active proposals MUST create no decision until disambiguated.
- **FR-014**: Direct same-event save MUST be supported only when the actual user event deterministically identifies the complete payload permitted by the upstream consent contract; otherwise the adapter MUST display a proposal and await a new decision.
- **FR-015**: Session end MUST expire unresolved candidates, unused grants, and session-only suppression state without persisting candidate content, while preserving already approved shared state.
- **FR-016**: Codex MUST access approved knowledge, controls, and guarded operations through the shared local expertiseOS service; the adapter MUST NOT expose unrestricted backend writes or duplicate approval, storage, retrieval, learning, or conflict logic.
- **FR-017**: expertiseOS adapter/service/search failures MUST NOT block ordinary Codex work; unverifiable or failed mutations MUST fail closed and MUST NOT report success.
- **FR-018**: Implementation readiness for write capability MUST depend on reproducible G0 evidence for automatic activation, actual-user capture, session identity, safe checkpoints, and failure-open behavior on the exact supported Codex version, OS, and permission mode; absent evidence, the adapter MUST remain accurately read-only.
- **FR-019**: The Codex behavior MUST be verified by contract fixtures and pinned live-host fixtures covering activation, bounded control loading, safe checkpoints, Save, Edit then Save, Skip, unrelated-message expiry, forged/model-only approval, session cleanup, service outage, shared retrieval, and capability degradation.

### Key Entities

- **Codex Host Session**: One active Codex session identity plus adapter identity, capability snapshot, atomic-operation depth, comparison-due state, active proposal reference, and last actual-user event reference; all volatile fields end with the session.
- **Normalized Host Event**: A host-neutral session, actual-user, atomic-operation, checkpoint, or end event derived from a verified Codex payload and carrying only the minimum identity/reference data needed by the shared contract.
- **Capability Snapshot**: The evidence-backed set of operations supported for an exact Codex version, operating system, installation surface, and permission mode.
- **Active Proposal Binding**: Volatile proposal ID, session ID, adapter ID, displayed digest, allowed actions, and expected versions used to interpret one actual-user response.
- **Codex Installation Registration**: Reversible host registration metadata needed to activate expertiseOS while preserving unrelated Codex configuration; it contains no candidate knowledge.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In all tested fresh supported Codex sessions after consented onboarding, expertiseOS activates automatically, connects to the intended local service, and reports the evidence-backed capability set.
- **SC-002**: Across all atomic-operation fixtures, zero expertiseOS learning or proposal prompts occur before the first verified safe checkpoint, and the underlying Codex task result remains intact.
- **SC-003**: Across all forged, model-only, tool-output, quoted, ambiguous, stale, cross-session, and cross-host decision fixtures, zero unauthorized decision grants or semantic writes occur.
- **SC-004**: Each clear Save event for one active proposal creates at most one matching decision, while Edit and Skip follow their specified lifecycle in every contract and supported live-host fixture.
- **SC-005**: In every service, retrieval, and write-failure fixture, ordinary Codex work completes independently and no failed or unverifiable mutation is reported as saved.
- **SC-006**: Session termination removes all unresolved Codex proposal and grant state in every fixture, with zero candidate marker tokens found in expertiseOS-controlled persistent storage.
- **SC-007**: Codex retrieves the same approved object IDs, versions, provenance, relationships, learner state, and controls exposed by the shared service, while every cross-session or cross-host approval reuse attempt is rejected.
- **SC-008**: Every claimed Codex capability has a reproducible fixture tied to an exact tested version, operating system, installation surface, and permission mode; all unproven claims are reported unavailable.

## Assumptions

- G0 owns selection and proof of the exact supported Codex mechanisms and versions; this feature consumes that evidence and does not infer support from documentation alone.
- The upstream HostAdapter contract supplies normalized event and capability types; the approval component supplies proposal, decision-grant, and guarded commit interfaces.
- Retrieval, control resolution, scope exclusions, and shared local service operations are supplied by their owning components and are called rather than reimplemented here.
- The shared behavioral skill and final cross-host acceptance wiring are integration-owned; this feature supplies Codex-specific adapter behavior and evidence fixtures only.
- Host-owned transcript/provider retention is outside expertiseOS-controlled persistence and is not treated as a substitute authorization channel.

## Out of Scope

- Approval-domain, candidate-store, persistence, backend mapping, retrieval ranking, learning-state, or Claude Code behavior.
- A Codex-only behavioral prompt, generic workflow engine, background scheduler, second model, natural-language authorization classifier, or unrestricted backend write surface.
- Private or undocumented Codex internals and speculative compatibility with untested host versions, remote Codex workers, or browser-only surfaces.
- Editing shared release or integration documentation; this component provides exact evidence for the integration owner to record.
