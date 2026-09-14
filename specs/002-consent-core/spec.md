# Feature Specification: Consent Core

**Feature Branch**: `002-consent-core`
**Created**: 2026-09-14
**Status**: Draft
**Input**: Domain types, volatile candidate lifecycle, exact user-decision grants, guarded knowledge mutations, optimistic versioning, approval receipts, and idempotent reconciliation for the expertiseOS MVP.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Save Exactly What Was Approved (Priority: P1)

As a user, I can approve a displayed knowledge proposal and trust that only that exact proposal, source scope, and version-bound operation becomes durable.

**Why this priority**: Explicit, exact approval is the central privacy and state-integrity boundary of expertiseOS.

**Independent Test**: With an in-memory proposal, a validated user event, and a conforming fake knowledge store, approve a create operation and verify the exact object/version and a matching minimal receipt are durable while the grant cannot be reused.

**Acceptance Scenarios**:

1. **Given** one active proposal awaiting a decision, **When** a real user Save event produces a matching one-use grant and the durable write and read-back succeed, **Then** the exact approved object is stored, one receipt references its version, the grant is consumed, and the proposal becomes approved.
2. **Given** clearly identified material in a direct user save instruction, **When** no material interpretation or additional semantic field is needed, **Then** one proposal and matching grant may be created from that event and committed through the same approval gate.
3. **Given** a user wants to edit displayed content, **When** the content changes, **Then** its digest is recomputed and a new matching user decision is required before commit.
4. **Given** an approved create, **When** it is read immediately by stable ID and version, **Then** content, categories, subjects, source scope, evidential status, contribution origin, and provenance match the approved proposal.

---

### User Story 2 - Reject Missing, Forged, or Stale Approval (Priority: P1)

As a user, I can rely on expertiseOS to reject model claims, tool text, quoted decisions, cross-session grants, modified proposals, and stale versions as authorization.

**Why this priority**: A convenient write path is unacceptable if a host model or unrelated event can bypass consent.

**Independent Test**: Attempt every mismatched or replayed authorization against a fake backend and verify no mutation or success receipt occurs.

**Acceptance Scenarios**:

1. **Given** a model argument, assistant message, or tool result says the user approved, **When** no grant from a validated host user event exists, **Then** the mutation is rejected without durable change.
2. **Given** a grant for another proposal, session, adapter, action, or content digest, **When** it is presented to the gate, **Then** it is rejected without durable change.
3. **Given** an object changed after a proposal captured its expected version, **When** commit is attempted, **Then** a version conflict is returned and the existing object is not overwritten.
4. **Given** a consumed grant or expired proposal, **When** it is replayed, **Then** it is rejected and a new displayed proposal and user event are required.

---

### User Story 3 - Decline or Leave Without Persistent Traces (Priority: P1)

As a user, I can skip, cancel, ignore, or leave a proposal knowing its unapproved content remains volatile and disappears when its interaction ends.

**Why this priority**: No-unapproved-persistence is a release-blocking privacy guarantee, including negative and crash paths.

**Independent Test**: Put a unique marker in candidate content, exercise every decline and expiry path, reconstruct the volatile stores, and confirm the marker never reaches any expertiseOS-controlled durable state.

**Acceptance Scenarios**:

1. **Given** a detected proposal, **When** it follows the legal path to awaiting a decision, **Then** its payload remains process-local throughout.
2. **Given** an awaiting proposal, **When** the user skips, cancels, sends an unrelated next message, ends the session, or the process restarts, **Then** the unresolved proposal cannot be committed and no candidate content is durable.
3. **Given** a declined candidate, **When** the same fingerprint occurs in the same session, **Then** a volatile suppression may prevent repetition; **When** a new session begins, **Then** that suppression is absent.
4. **Given** an illegal candidate-state transition, **When** it is attempted, **Then** it fails without altering the candidate or durable state.

---

### User Story 4 - Safely Reconcile Interrupted Writes (Priority: P2)

As a user, I receive a truthful result when durable storage or receipt recording fails, and a bounded retry never duplicates an already-written object.

**Why this priority**: Partial failures must not create duplicate knowledge or false Saved messages.

**Independent Test**: Inject failures before the canonical write, after the canonical write but before receipt completion, and during a retry; verify deterministic recovery by `operation_id`.

**Acceptance Scenarios**:

1. **Given** a valid approval, **When** the durable knowledge write fails, **Then** no success receipt is created, no success is reported, and the active interaction may retry with the same `operation_id`.
2. **Given** the knowledge write and read-back succeeded but receipt storage failed, **When** the same operation is retried, **Then** the existing exact object is reconciled, the missing receipt is completed, and no duplicate object/version is created.
3. **Given** the backend returns content or version different from the approved write on read-back, **When** commit is finalized, **Then** success is withheld and the grant is not consumed as a completed authorization.
4. **Given** an interrupted operation is reconciled, **When** the same `operation_id` is submitted again, **Then** the previously completed result is returned without another semantic mutation.

---

### User Story 5 - Make Versioned Semantic Changes Without Erasing Disagreement (Priority: P2)

As a user, I can approve revisions, relationships, conflict resolutions, and retirement while stable identities, lineage, provenance, and contradictory claims remain inspectable.

**Why this priority**: Later components depend on one guarded, host-neutral mutation contract rather than special bypasses.

**Independent Test**: Using existing approved objects in the fake backend, propose and approve revision, relationship, and retirement operations; verify expected-version enforcement, version increments, stable IDs, and traceable coexistence of conflicts.

**Acceptance Scenarios**:

1. **Given** an approved object at version N, **When** a matching revision is approved, **Then** the same stable object ID has version N+1 and preserved lineage.
2. **Given** two contradictory approved claims, **When** no explicit conflict-resolution change is approved, **Then** both remain available and neither is silently overwritten.
3. **Given** a proposed relationship addition, removal, or change, **When** no exact approval exists, **Then** the relationship is unchanged.
4. **Given** a retirement proposal, **When** it is approved against the current version, **Then** status changes to retired without being treated as deletion.
5. **Given** categorize, split, or merge organization, **When** approved, **Then** it is composed from displayed version-bound semantic operations and does not silently delete disagreement.

### Edge Cases

- Multiple active proposals make an otherwise generic Save or yes ambiguous; no grant is issued until one proposal is identified.
- Blank content, missing subjects for approved knowledge, non-positive versions, unknown relation types, or unstable relationship targets are rejected by domain validation.
- A late user decision for a declined or expired proposal cannot reactivate it.
- A grant becomes invalid when the displayed payload or any expected object version changes.
- Two hosts proposing changes to the same object race through the same optimistic-version rule; the stale commit conflicts.
- Candidate payloads, unused grants, unrelated prompt text, and full source material have no durable-state serialization path.
- Source disappearance preserves the approved reference with unavailable status; it does not manufacture replacement evidence.
- A technical retry or index maintenance event is not interpreted as a new user decision or semantic revision.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define host-neutral domain values for the six knowledge categories, three knowledge subjects, knowledge status, contribution origin, seven relationship types, candidate state, pending operation kind, user decision action, and learner state.
- **FR-002**: Approved knowledge MUST have non-blank content, at least one subject, a stable ID, a positive monotonically increasing semantic version, active or retired status, contribution origin, and inspectable approved source references; categories MAY be empty.
- **FR-003**: The candidate lifecycle MUST allow forward progress from `detected -> awaiting_checkpoint -> awaiting_decision`, approval only from `awaiting_decision`, and termination from any unresolved state to `declined` or `expired`; all other transitions MUST be rejected.
- **FR-004**: Candidate payloads, unresolved proposals, unused decision grants, and same-session decline suppression MUST remain in process memory and MUST be absent after store reconstruction or process restart.
- **FR-005**: Session end, loss of context, explicit cancellation, or an unrelated next user message MUST expire unresolved candidates; a late decision MUST require a new proposal.
- **FR-006**: A decision grant MUST be created only from a validated host user event and MUST bind one proposal, session, adapter, action, content digest, user-event reference, and creation time.
- **FR-007**: A decision grant MUST authorize at most one proposal resolution, MUST expire with its proposal/session, and MUST reject reuse or mismatch by proposal, session, adapter, action, or digest.
- **FR-008**: The system MUST calculate one deterministic canonical digest over the displayed semantic fields, including operation kind, content and shown metadata, approved source scope, relationship changes, and relevant expected versions, while excluding timestamps and random identifiers.
- **FR-009**: Before any semantic mutation, the approval gate MUST validate the active proposal state, session, adapter, unconsumed grant, decision action, exact digest, current expected versions, and domain-operation validity.
- **FR-010**: The guarded commit MUST require the submitted `operation_id` to match the active proposal, then order successful work as approval validation, explicit durable mutation with that canonical `operation_id`, exact read-back, minimal approval-receipt storage, grant consumption, candidate approval, and only then success reporting.
- **FR-011**: A failed durable mutation or failed exact read-back MUST create no success receipt and MUST report no false success.
- **FR-012**: If the durable mutation succeeded but receipt storage did not, a bounded retry with the same `operation_id` MUST reconcile the existing mutation and complete the receipt without duplicating the object or semantic version.
- **FR-013**: Each successful semantic mutation MUST produce one minimal receipt containing operation and proposal IDs, operation kind, affected object IDs/versions, canonical digest, user-event reference, adapter ID, and timestamp, without candidate content or unrelated prompt text.
- **FR-014**: The guarded knowledge service MUST provide proposal, decline, commit, and approved-read operations without exposing an unrestricted backend mutation path to host-facing callers.
- **FR-015**: Create, revision, relationship change, conflict resolution, categorization, split, merge, retirement, and deletion proposals MUST use the same approval and version-binding primitives; this component implements create, revision, relationship change, retirement, and grouped approval binding for organization, while preserving compatible contracts for later deletion integration. Grouped effects MUST use deterministic child `operation_id` values derived from the approved parent `operation_id` and ordered effect identity.
- **FR-016**: Every semantic revision MUST verify captured expected versions and increment the affected object's version; stale writes MUST conflict rather than overwrite.
- **FR-017**: Relationship mutations MUST use stable source and target IDs, supported relationship types, relevant expected versions, and approved relationship provenance.
- **FR-018**: Contradictory approved claims MUST coexist unless an exact displayed resolution is approved; semantic consolidation MUST NOT occur silently.
- **FR-019**: A direct save instruction MAY create a proposal and grant from one actual user event only when the identified material and scope are deterministic and no new semantic claims, categories, relations, or excerpts are inferred; otherwise a newly displayed proposal and decision are required.
- **FR-020**: Approved provenance MUST be limited to shown source scope and MAY include host/session/event references, artifact locator, approved excerpt, date/checksum, accessibility status, and contribution origin; hidden reasoning and full unrelated sources MUST NOT be stored.
- **FR-021**: The SQLite base state MUST persist approval receipts and, only if required for reconciliation, a content-free operation journal keyed by `operation_id`; learner and control tables are excluded from this component.
- **FR-022**: A backend or state-store failure MUST block only the unsafe knowledge mutation, preserve ordinary host work, and return a truthful non-success or incomplete result.
- **FR-023**: Saving knowledge MUST NOT create learner evidence or advance mastery; C004's separate learner-state projection treats an object with no qualifying approved evidence as `new`.
- **FR-024**: Every dataclass introduced by this component MUST require callers to supply every field explicitly; defaults belong at construction call sites, not dataclass field definitions.

### Key Entities

- **KnowledgeObject**: Versioned approved semantic content with stable identity, optional categories, one or more subjects, scope/status/evidential metadata, provenance, contribution origin, and timestamps.
- **SourceReference**: Approved, bounded provenance pointing to a host event, conversation, file, artifact, tool result, user reflection, or user-provided source, with accessibility status.
- **Relationship**: A version-aware semantic link between stable knowledge IDs with one supported type and optional approved explanation/provenance.
- **PendingOperation**: An in-memory proposal containing proposal identity, canonical `operation_id`, host session/adapter ownership, operation kind, lifecycle state, volatile payload, canonical digest, expected versions, and creation time.
- **DecisionGrant**: One-use, in-memory authorization derived from an actual host user event and exactly bound to a pending operation decision.
- **ApprovalReceipt**: Minimal durable evidence written only after an exact approved mutation succeeds and is read back.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of Save cases, the durable object and receipt digest match the displayed approved semantic payload and affected versions.
- **SC-002**: All defined forged, ambiguous, cross-proposal, cross-session, cross-adapter, modified-content, stale-version, expired, and replayed approval cases produce zero semantic mutations and zero success receipts.
- **SC-003**: Skip, cancel, unrelated-message, session-end, and process-restart cases leave a unique candidate marker absent from every expertiseOS-controlled durable record owned by this component.
- **SC-004**: Retrying an operation after a canonical-write/receipt interruption produces exactly one object or semantic version and exactly one matching receipt.
- **SC-005**: Every legal candidate transition succeeds and every illegal transition fails without changing durable state.
- **SC-006**: Concurrent commits against the same expected object version yield one accepted semantic revision and a conflict for every stale contender, with no last-write-wins overwrite.
- **SC-007**: Create, revision, relationship, and retirement scenarios preserve stable IDs, approved provenance, and inspectable conflicting claims on immediate read-back.
- **SC-008**: Unit, integration-level fake-backend, type, and static checks cover the guarded producer-to-consumer path and all release-blocking negative cases before this component is promoted.

## Assumptions

- C001 provides the installable Python 3.12 package, `HostAdapter` and `KnowledgeBackend` contracts, a conforming fake backend/host, pytest configuration, and the finalized model/validation-library choice.
- Host adapters alone validate actual user-input provenance and request grant registration; this component validates normalized event-bound fields without parsing host-specific events.
- The Basic Memory mapping, retrieval implementation, real-backend round trips, index behavior, and deletion cleanup belong to C003/C007; this component tests against C001 fakes.
- SQLite stores receipts and content-free reconciliation metadata only in this component. C004 requests learner/control schema additions through the consent owner after reconciliation.
- One local service serializes access to the SQLite state store; cross-host semantic concurrency is governed by backend expected versions rather than distributed locking.
- Timestamps are UTC, and IDs including `operation_id` values are opaque stable values supplied explicitly at object construction.

## Out of Scope

- Live Basic Memory mapping, search, recall, indexing, and keyword fallback.
- Learner evidence behavior, mastery calculation, learning controls, and deferred activities.
- Codex or Claude Code event parsing, onboarding, and production adapter behavior.
- Export, restore, deletion cleanup, uninstall, full outage recovery, and final MCP/service wiring.
- Cloud synchronization, a second generative model, autonomous background work, generic workflow/policy engines, and speculative compatibility layers.
