# Feature Specification: Claude Code Host Adapter

**Intent**: Define the supported Claude Code experience that connects users to the shared local expertiseOS service without duplicating domain policy or weakening consent.

**Feature Branch**: `006-claude-host`
**Created**: 2026-09-14
**Status**: Draft
**Input**: Claude Code onboarding, activation, normalized lifecycle events, actual-user decision registration, safe checkpoints, proposal expiry, capability reporting, shared local service use, and failure-open host behavior.

## User Scenarios & Testing

### User Story 1 - Start expertiseOS in Claude Code (Priority: P1)

After one guided onboarding flow, a user starts a supported Claude Code session and expertiseOS activates against the same local service and repository used by other supported hosts. The user sees accurate support limitations and does not configure another model key, database, or embedding provider.

**Why this priority**: No other Claude integration behavior is usable until setup is safe, reversible, and truthful about the installed host's capabilities.

**Independent Test**: In a fresh supported fixture, complete onboarding, start Claude Code, verify activation and service health, preserve unrelated host configuration, and reverse only the expertiseOS registration during uninstall.

**Acceptance Scenarios**:

1. **Given** a pinned supported Claude Code installation and completed onboarding consent, **When** a new session starts, **Then** expertiseOS activates automatically and points to the configured shared local service.
2. **Given** unrelated existing Claude Code configuration, **When** expertiseOS is installed or removed, **Then** that configuration remains unchanged.
3. **Given** a host/version whose required integration event is not proven, **When** setup reports capabilities, **Then** the unsupported capability is explicit and write capability is disabled when actual-user decision validation is unavailable.
4. **Given** a fresh setup, **When** the user completes onboarding, **Then** no second LLM key, manual database work, or embedding-provider configuration is requested.

---

### User Story 2 - Continue work through safe checkpoints (Priority: P1)

While Claude Code performs normal work, the adapter translates supported host lifecycle events into the shared host-neutral contract. expertiseOS may act only at an eligible checkpoint and never interrupts an incomplete atomic operation.

**Why this priority**: The host must retain ownership of task execution, including when expertiseOS is unavailable.

**Independent Test**: Replay pinned Claude events for session start, a bounded multi-step operation, checkpoint, and session end; verify normalized ordering, checkpoint eligibility, control/exclusion checks, and uninterrupted host completion during service failure.

**Acceptance Scenarios**:

1. **Given** an atomic operation is open, **When** Claude emits intermediate supported events, **Then** no expertiseOS learning or collection prompt is eligible until the operation finishes and a supported checkpoint occurs.
2. **Given** current controls or a matching scope exclusion forbid observation, **When** a host event contains source context, **Then** the adapter does not forward that context for candidate detection.
3. **Given** the local service is unavailable or returns an error, **When** Claude continues the user's task, **Then** ordinary task work completes and no failed mutation is presented as saved.
4. **Given** a session ends, **When** the adapter handles the end event, **Then** the core is instructed to expire unresolved proposals and grants for that session without persisting candidate recovery content.

---

### User Story 3 - Authorize an exact proposal from real user input (Priority: P1)

When one active expertiseOS proposal is displayed in Claude Code, the user's clear Save, Edit, or Skip response is observed through a verified actual-user input path and translated into a decision observation bound to that proposal, session, adapter, displayed digest, and expected versions.

**Why this priority**: A host adapter is write-capable only if it can distinguish the user's decision from assistant, model, and tool output.

**Independent Test**: With one active proposal, replay actual user decisions and adversarial non-user events; verify that only a fresh, unambiguous, matching user event reaches C002 grant registration and that it can be consumed once.

**Acceptance Scenarios**:

1. **Given** one active proposal and a matching actual-user Save event, **When** the adapter validates it, **Then** it submits one observation containing the exact proposal, session, adapter, action, digest, expected versions, and opaque user-event reference required by the shared consent boundary.
2. **Given** assistant output, tool output, model arguments, generic tool permission, quoted Save text, an unrelated yes, another session, another host, a stale proposal, or a changed digest, **When** it reaches the adapter, **Then** no decision grant is requested.
3. **Given** an Edit response containing final content, **When** it is processed, **Then** the revised content is re-displayed with a new digest and requires a fresh matching Save event before commit.
4. **Given** an unrelated next user event or session end, **When** an active proposal remains unresolved, **Then** the proposal expires and cannot be approved later.
5. **Given** a direct user instruction to save clearly identified material, **When** deterministic identification is possible under C002 rules, **Then** the adapter may submit the same-event direct-save observation; otherwise it displays a proposal and waits for a later decision.

---

### User Story 4 - Recall shared approved knowledge safely (Priority: P2)

A Claude Code session uses the same local service as Codex to retrieve bounded, approved knowledge and current control state. Host switching never transfers proposal authorization or creates learning evidence.

**Why this priority**: Shared approved state provides cross-host continuity, while pending authorization must remain isolated to its originating session.

**Independent Test**: Point Claude and a fake second host at one service; verify identical approved IDs and versions, bounded untrusted retrieval, isolated proposal decisions, and safe version conflicts.

**Acceptance Scenarios**:

1. **Given** approved knowledge created through another host, **When** Claude retrieves it, **Then** the same stable ID, version, provenance, relationships, conflict indicators, learner-state reference, and control state are available through bounded service responses.
2. **Given** an active proposal from another host or session, **When** a Claude user event says Save, **Then** it cannot authorize that proposal.
3. **Given** a stale expected version, **When** Claude submits an otherwise authorized mutation, **Then** the shared service reports conflict and the adapter does not overwrite or claim success.
4. **Given** recalled content containing instructions, **When** Claude receives it, **Then** it is labeled and handled as untrusted data, never as approval, control, or tool authority.

### Edge Cases

- A host event arrives before session start, after session end, or with mismatched adapter/session identity: reject or ignore it without changing shared state.
- Nested or overlapping supported atomic events occur: prompt eligibility resumes only when the normalized atomic depth returns to zero.
- The host lacks an explicit atomic-begin event: use only the narrowest G0-proven post-operation checkpoint and expose the limitation.
- Multiple proposals appear active: require explicit itemized decisions or disambiguation; never infer one broad approval.
- Service timeout occurs after a decision observation: preserve the host task result, show no Saved claim, and rely on C002 idempotency for an exact retry while the interaction remains active.
- Capability evidence is absent, stale, or for another host version/OS: report the capability unavailable for the running environment.
- Pause, fatigue rest, target-satisfied, disable, and scope-exclusion responses differ: consume C004's resolved booleans rather than recreating precedence in the adapter.
- Host-owned transcript retention may contain user text: do not claim that expertiseOS controls or deletes host-owned data.

## Requirements

### Functional Requirements

- **FR-001**: The adapter MUST support automatic activation after consented onboarding only for a pinned Claude Code version, operating system, registration mechanism, and permission mode with passed feasibility evidence.
- **FR-002**: Installation and removal MUST preserve unrelated Claude Code configuration and MUST use supported public integration mechanisms.
- **FR-003**: The adapter MUST report `can_read`, `can_search`, `can_validate_user_decisions`, `can_write`, `can_observe_atomic_boundaries`, and `can_auto_activate` independently with evidence references and limitations.
- **FR-004**: The adapter MUST set `can_write=false` whenever actual-user decision validation is unavailable for the active host/version/environment.
- **FR-005**: The adapter MUST translate only supported Claude Code payloads into host-neutral session start, actual user input, atomic begin, atomic end, safe checkpoint, and session end events.
- **FR-006**: Raw Claude Code payload parsing and vendor event types MUST remain inside the Claude adapter; downstream services MUST receive only the shared C001 contract values.
- **FR-007**: The adapter MUST maintain only the minimal volatile session state needed for normalized identity, atomic depth, comparison due state, active proposal binding, and last user-event reference.
- **FR-008**: The adapter MUST consult C004 control resolution and scope exclusions before forwarding source content for observation, candidate comparison, collection prompts, proactive exercises, or recall.
- **FR-009**: The adapter MUST mark a checkpoint eligible only when no normalized atomic operation remains open and the applicable control resolution permits the requested interaction.
- **FR-010**: The adapter MUST NOT invoke fresh semantic analysis after every low-level event; it MUST defer comparison to an eligible supported checkpoint.
- **FR-011**: Only a G0-verified actual Claude user-input event MAY produce a C001 decision observation for C002 grant registration.
- **FR-012**: A decision observation MUST match the active proposal's ID, operation, adapter, session, displayed digest, expected versions, allowed action, and opaque actual-user event reference.
- **FR-013**: Assistant/model/tool output, generic tool permission, quoted prior text, ambiguous response, stale identity, cross-session event, cross-host event, or changed content MUST NOT request a decision grant.
- **FR-014**: Save and Skip MUST be recognized only through deterministic unambiguous controls; ambiguous language MUST require clarification and a later clear user event.
- **FR-015**: An Edit with final content MUST replace and re-display the active proposal with a recomputed digest; it MUST NOT authorize persistence until a later matching Save.
- **FR-016**: An unrelated next user event or session end MUST expire the unresolved proposal through C002 lifecycle operations and make any associated unconsumed grant unusable.
- **FR-017**: Same-event direct save MUST be limited to material deterministically identified by the actual user event and its immediate active reference, without adding semantic content the user did not identify.
- **FR-018**: The adapter MUST use the configured shared local service for reads, search, proposal lifecycle, decisions, controls, and approved writes; it MUST NOT access the knowledge backend or SQLite directly.
- **FR-019**: Approved retrieval returned to Claude MUST remain bounded, provenance-aware, conflict-preserving, exclusion-filtered, explicitly health-labeled, and marked as untrusted data.
- **FR-020**: Service, retrieval, hook, or mutation failure MUST leave ordinary Claude task work available, stop unsafe memory writes, and never produce a false Saved result.
- **FR-021**: The adapter MUST NOT treat host switching, retrieval, task completion, or assistant output as learner evidence or mastery change.
- **FR-022**: The adapter MUST load only compact controls, capabilities, and task-relevant bounded approved context, never the complete repository or unrelated user prompts.
- **FR-023**: Implementation support claims MUST be backed by reproducible fixtures recording Claude Code version, OS, permission mode, supported event names, session identity behavior, registration/uninstall steps, command or manual procedure, result, and limitation.

### Key Entities

- **Claude Host Session**: A volatile adapter-scoped view of the active host session, normalized identity, atomic depth, comparison status, and active proposal reference.
- **Claude Event Evidence**: A sanitized fixture record connecting a supported raw Claude event to one normalized C001 event without retaining unrelated prompt content.
- **Capability Report**: The six independently evaluated C001 host capability facts for the exact tested environment, each with evidence and limitations.
- **Decision Binding**: The C001 value carrying proposal identity, operation, adapter/session, displayed digest, expected versions, and allowed actions.
- **Decision Observation**: The adapter output that either matches one verified actual-user event or gives a typed rejection; it is not a durable grant.

## Success Criteria

### Measurable Outcomes

- **SC-001**: On a fresh pinned supported fixture, one onboarding flow activates expertiseOS in a new Claude Code session, uses the configured shared local service, and removes its registration without changing unrelated host configuration.
- **SC-002**: The adapter contract suite maps every supported session, user, atomic, checkpoint, and end fixture to the expected C001 event with 100% deterministic pass results.
- **SC-003**: In all forged and ambiguous approval fixtures, zero events request a grant; one fresh exact actual-user Save fixture requests one matching grant and one authorized commit succeeds exactly once.
- **SC-004**: Across every bounded atomic-operation fixture, zero expertiseOS prompts become eligible before normalized atomic depth returns to zero and a supported checkpoint occurs.
- **SC-005**: Skip, unrelated-message, session-end, and restart fixtures leave zero candidate markers in expertiseOS-controlled durable stores and cannot approve the expired proposal.
- **SC-006**: During forced local-service failure, the reference Claude task completes in every fixture, no unsafe write occurs, and no Saved result is displayed.
- **SC-007**: Capability output matches the pinned evidence for every tested environment; environments without verified actual-user capture report `can_write=false` in every run.
- **SC-008**: Cross-host integration returns the same approved object ID/version to Claude and rejects 100% of cross-host/cross-session approval attempts and stale writes.
- **SC-009**: Observation-disabled and excluded-scope fixtures forward zero protected source content to candidate detection or retrieval consumers.
- **SC-010**: Claude-facing retrieval never exceeds the requested limit or 20 items, labels every result as untrusted data, and exposes degraded/unavailable health without blocking ordinary work.

## Assumptions

- C001's `HostAdapter`, `HostEvent`, `HostCapability`, `DecisionBinding`, and `DecisionObservation` contracts are integrated before implementation starts.
- C002 owns proposal lifecycle, decision grants, exact digest/version validation, idempotent commit, and truthful result status.
- C003 owns bounded retrieval and canonical backend access; C006 consumes only its service-facing response.
- C004 owns control precedence and scope-exclusion matching; C006 consumes the resolved permissions.
- C008 owns the shared behavioral skill and full cross-host acceptance wiring; C006 supplies Claude-specific fixtures and adapter behavior.
- The exact supported Claude Code version, event mappings, install mechanism, permission mode, session identity, and OS remain blocked until C001 G0 evidence passes. No compatibility claim is inferred from documentation alone.

## Out of Scope

- Domain, proposal, approval, grant, backend, retrieval-ranking, learning, mastery, or control-policy implementation.
- Codex adapter behavior or a second Claude-specific behavioral prompt.
- Direct Basic Memory or SQLite access from the adapter.
- Private or undocumented Claude Code internals, transcript polling, timing heuristics, background harvesting, or a separate scheduler.
- Unrestricted host-facing write tools, cloud synchronization, a second generative model, or speculative compatibility layers.
