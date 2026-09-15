# Feature Specification: Learner Evidence and Learning Controls

**Intent**: Define the smallest inspectable learner-state and control behavior required by the expertiseOS MVP without adding autonomous tutoring or weakening approval.

**Feature Branch**: `004-learning-controls`

**Created**: 2026-09-14

**Status**: Draft

**Input**: Learner evidence, deterministic mastery, reflection targets, effort, pause/fatigue/target/disable precedence, scope exclusions, inspection, and deferred activities from the approved MVP plan.

## Clarifications

### Session 2026-09-14

- Q: May `partial` evidence advance demonstrated mastery, and how adjustable should advancement counts be? -> A: Only `pass` advances; other outcomes contribute zero. Positive integer pass-count thresholds are adjustable per transition, remain nondecreasing, and cannot bypass autonomous safeguards.

## User Scenarios & Testing

### User Story 1 - Approve Evidence and Inspect Mastery (Priority: P1)

As a learner, I can approve evidence of my own contribution and inspect the resulting mastery state for the relevant saved knowledge version and scope, so that expertiseOS does not confuse saving or assistant work with my understanding.

**Why this priority**: Trustworthy learner state is the base for every later learning adjustment.

**Independent Test**: Submit representative approved and rejected evidence against an existing approved knowledge object, then inspect the evidence history and deterministic state summary.

**Acceptance Scenarios**:

1. **Given** a newly approved knowledge object with no qualifying evidence, **When** its learner state is inspected, **Then** the state is `new`.
2. **Given** an assistant-only explanation or a successful artifact with unknown user contribution, **When** evidence is proposed, **Then** no demonstrated-mastery advance occurs.
3. **Given** a materially correct user explanation and matching approval, **When** the evidence is recorded, **Then** the evidence and resulting `explained` state are inspectable for that object version and scope.
4. **Given** the user rejects or corrects a proposed assessment, **When** the proposal is resolved, **Then** the rejected assessment causes no durable learner-state change and corrected content requires matching approval.
5. **Given** knowledge is revised or its applicability boundary changes, **When** mastery is inspected, **Then** older evidence is retained but does not silently prove mastery for an inapplicable version or scope.

---

### User Story 2 - Reach Mastery Deterministically (Priority: P1)

As a learner, I receive only mastery states justified by approved evidence, including a narrowly defined autonomous state, so that reduced scaffolding reflects demonstrated performance rather than a score or guess.

**Why this priority**: Incorrect mastery claims can remove needed support and violate the product's evidence boundary.

**Independent Test**: Feed approved evidence histories covering recognition through transfer and all autonomous boundary cases into the summary behavior and verify the exact state.

**Acceptance Scenarios**:

1. **Given** qualifying approved `pass` evidence, **When** learner state is summarized using the active pass-count thresholds, **Then** the highest justified state is one of `new`, `recognized`, `explained`, `applied`, `transferred`, or `autonomous`.
2. **Given** at least the configured number of independent successful demonstrations, never fewer than two, on distinct tasks and in separate sessions, at least one meaningful transfer, no unresolved relevant contradiction, and explicit user agreement to reduce scaffolding, **When** state is summarized, **Then** `autonomous` is justified within the evidence scope.
3. **Given** any autonomous condition is missing, including distinct tasks, separate sessions, transfer, contradiction resolution, or agreement, **When** state is summarized, **Then** `autonomous` is not assigned.
4. **Given** self-reported familiarity without qualifying demonstrated evidence, **When** state is summarized, **Then** self-report remains distinct and does not advance demonstrated mastery.
5. **Given** an authorized threshold change, **When** state is summarized, **Then** positive integer thresholds remain nondecreasing by state and cannot reduce autonomous below two independent passes or remove its task, session, transfer, contradiction, or agreement safeguards.

---

### User Story 3 - Control Learning Without Blocking Work (Priority: P1)

As a user, I can configure reflection targets, effort, pauses, rest, exclusions, and full disable, with predictable precedence, while ordinary host work and allowed recall behave correctly.

**Why this priority**: These controls determine whether the product respects attention, fatigue, privacy, and explicit user intent.

**Independent Test**: Evaluate every control condition and combination at period boundaries, including target reached, fatigue, pause, exclusion, and disable, and assert observation, collection, proactive learning, and recall permissions separately.

**Acceptance Scenarios**:

1. **Given** the reflection target is satisfied, **When** an eligible observation occurs, **Then** collection may continue and approved recall remains available, but proactive exercises stop for the current period.
2. **Given** explicit pause is active, **When** the user continues ordinary work or requests one explanation, **Then** proactive collection and learning remain suspended, approved recall remains available, and the request does not resume collection.
3. **Given** fatigue is reported before target completion, **When** control state is resolved, **Then** unresolved candidates expire, proactive detection and exercises stop, approved recall remains available, the target remains unmet, and rest lasts until its configured or user-selected end.
4. **Given** expertiseOS is disabled, **When** work continues, **Then** expertiseOS performs no observation, collection, learning, or recall.
5. **Given** pause, fatigue rest, and target satisfaction overlap, **When** control state is resolved, **Then** disable takes precedence over pause, pause takes precedence over fatigue rest, fatigue rest takes precedence over target satisfaction, and the active reason remains inspectable.
6. **Given** a new target period begins during a pause, **When** counters roll over, **Then** the pause remains active.
7. **Given** a source, path, or session scope is excluded, **When** observation or retrieval is considered for that scope, **Then** source content is not sent for candidate detection and excluded objects or context are not returned into that task.

---

### User Story 4 - Count Reflection and Defer Approved Work (Priority: P2)

As a learner, I can see consistent reflection progress and defer a learning activity tied only to approved knowledge for a later active foreground session.

**Why this priority**: Progress and deferment are useful only after evidence and control behavior is trustworthy.

**Independent Test**: Record approved reflection activities of different sizes, retry the same activity, reach the effort limit, and create/remove deferred activities under active and suspended control states.

**Acceptance Scenarios**:

1. **Given** a saved reflection with meaningful user contribution connected to approved knowledge or evidence, **When** progress is recorded, **Then** it counts once even if it produced several linked objects or is retried.
2. **Given** a user response qualifies for multiple effort categories, **When** effort is recorded, **Then** only the highest applicable value among 0.25, 1.0, and 2.0 units is counted.
3. **Given** raw logs, repeated paraphrases, assistant-only output, mere relabeling, or ordinary task activity, **When** progress is evaluated, **Then** neither a qualifying reflection nor user-response effort is counted.
4. **Given** the effort limit is reached before the target, **When** control state is resolved, **Then** fatigue rest starts and no final exercise is requested merely because the target remains unmet.
5. **Given** a deferred activity references approved object IDs and versions and the user explicitly chooses to defer it, **When** it is saved, **Then** it can be offered only in a later foreground session while learning is active.
6. **Given** a deferred activity contains unapproved free-form knowledge or has no approved reference, **When** persistence is attempted, **Then** it is rejected.

### Edge Cases

- `insufficient_evidence` records uncertainty and does not act as failure or advance mastery.
- Higher-quality approved evidence may justify skipping elementary states, but only within its knowledge version and scope.
- `partial`, `fail`, and `insufficient_evidence` remain inspectable and contribute zero toward every advancement threshold.
- Repeated success on the same task or within the same session cannot satisfy the autonomous heuristic.
- An unresolved contradiction relevant to the claimed scope blocks `autonomous` even when demonstration counts are met.
- Period rollover resets only the relevant aggregate counters; it does not cancel pause, rest, exclusions, or disable.
- A reflection that creates multiple approved linked objects is still one qualifying activity.
- Duplicate delivery of one evidence, reflection, or effort event is idempotent and does not double-count across hosts.
- Changing exclusions, targets, limits, pause, or enablement is durable user-owned state and requires the existing approval boundary.
- Retrieval degradation or failure does not modify learner evidence, mastery, or counters.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST persist learner evidence only after the existing approval service authorizes the exact proposed evidence and state change.
- **FR-002**: Learner evidence MUST identify the approved knowledge ID and version, task, criterion, outcome, assistance level, applicable scope, user contribution, proposed and approved states, approval receipt, and creation time.
- **FR-003**: Evidence outcomes MUST distinguish `pass`, `partial`, `fail`, and `insufficient_evidence`; only `pass` evidence may contribute to advancement, while all other outcomes remain inspectable and contribute zero.
- **FR-004**: Saving knowledge, assistant-only output, unknown user contribution, retrieval frequency, task success without attributable contribution, and self-reported familiarity MUST NOT independently advance demonstrated mastery.
- **FR-005**: The system MUST derive one inspectable learner state per approved knowledge version and scope from approved evidence using only `new`, `recognized`, `explained`, `applied`, `transferred`, and `autonomous`, selecting the highest state whose evidence kind and active pass-count threshold are satisfied.
- **FR-006**: The mastery summary MUST retain evidence history when knowledge changes and MUST prevent evidence outside the current version or applicability scope from silently justifying the current state.
- **FR-007**: The `autonomous` state MUST require the configured autonomous pass-count threshold, which MUST be at least two approved independent successful demonstrations, plus distinct tasks, separate sessions, at least one meaningful transfer, no unresolved relevant contradiction, and explicit user agreement to reduce scaffolding.
- **FR-008**: The system MUST keep self-reported familiarity separate from demonstrated mastery and MUST NOT produce a global seniority or psychometric score.
- **FR-009**: The system MUST support a daily or weekly reflection period, a configurable reflection target, an effort limit, a rest interval, explicit pause/resume, enable/disable, and source/path/session scope exclusions.
- **FR-010**: Defaults MUST be daily in the local device timezone, one reflection per day, a three-per-week preset, a six-unit effort limit, a 60-minute rest interval, and pass thresholds `1, 1, 1, 1, 2` from recognized through autonomous.
- **FR-011**: One user response MUST count at most one effort value: 0.25 for a simple collection or organization decision, 1.0 for a brief recall, explanation, or application response, or 2.0 for a substantial multi-step reflection response.
- **FR-012**: Ordinary task activity and model-only output MUST NOT consume effort.
- **FR-013**: A qualifying reflection MUST count once only when meaningful user contribution develops reusable knowledge, connects to approved knowledge or evidence, and is saved with approval; multiple linked outputs and retries MUST NOT multiply the count.
- **FR-014**: Control resolution MUST apply this precedence: disabled, explicit pause, active fatigue rest, target satisfied, ordinary active learning.
- **FR-015**: Target satisfaction MUST stop proactive exercises for the current period while allowing collection and approved recall.
- **FR-016**: Pause and fatigue rest MUST stop proactive detection prompts and learning while allowing approved recall; pause MUST survive target-period rollover, and one-off explanation requests MUST NOT resume collection.
- **FR-017**: Fatigue reporting MUST expire unresolved candidates, preserve an unmet target, and start the configured rest interval unless the user selected another supported duration.
- **FR-018**: Disable MUST stop all expertiseOS observation, collection, learning, and recall while leaving ordinary host work unaffected.
- **FR-019**: Scope exclusions MUST be checked before candidate-detection input and before retrieval is returned to the current task; exclusion changes MUST use the existing approval boundary.
- **FR-020**: The system MUST expose bounded read-only inspection of current learner state and the approved evidence that supports it, plus current controls, active reason, period progress, effort, and deferred activities.
- **FR-021**: A deferred activity MUST contain only an ID, approved knowledge ID/version references, activity type, creation time, and status; creation MUST require an explicit defer decision and MUST reject unapproved free-form knowledge.
- **FR-022**: Deferred activities MUST be offered only in a later foreground session when learning is active and MUST support explicit removal.
- **FR-023**: Evidence, reflection, and effort recording MUST be idempotent so repeated delivery and cross-host retrieval cannot double-count the same approved activity.
- **FR-024**: Durable learner evidence, mastery changes, counters, controls, exclusions, and deferred-activity changes MUST use the upstream approval and state contracts; this component MUST NOT create an alternate write path.
- **FR-025**: The system MUST support explicitly instantiated positive integer pass-count thresholds for `recognized`, `explained`, `applied`, `transferred`, and `autonomous`; thresholds MUST be nondecreasing in that order, changes MUST use the existing approval/state boundary, and numeric values MUST NOT bypass state-specific evidence meanings or any autonomous non-numeric safeguard.

### Key Entities

- **Learner Evidence**: An approved record of attributable user performance tied to one approved knowledge object version, task, criterion, assistance level, and scope.
- **Learner State Summary**: A deterministic, inspectable result derived from approved evidence for one knowledge version and scope; it may be regenerated rather than treated as independent truth.
- **Advancement Thresholds**: User-owned positive integer pass counts for each demonstrated learner-state transition, ordered monotonically and constrained by the autonomous minimum and safeguards.
- **Control Settings**: User-owned target period, reflection target, effort limit, rest interval, pause, enablement, and exclusions.
- **Period Progress**: Idempotent aggregate reflection and effort counts for one daily or weekly period in the local device timezone.
- **Deferred Activity**: Minimal user-approved foreground work containing references to approved knowledge versions and no candidate claim text.
- **Control Resolution**: The effective behavior and reason resulting from the current settings, time, target progress, and fatigue state.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All negative evidence cases in AT-07 and AT-09 leave demonstrated mastery unchanged in deterministic tests.
- **SC-002**: Every enumerated single and overlapping combination of disable, pause, fatigue rest, target satisfaction, and ordinary activity resolves to the documented precedence and permissions in deterministic tests.
- **SC-003**: The autonomous state is produced in the complete qualifying case and withheld in every single-condition-missing boundary case.
- **SC-004**: Duplicate delivery of the same evidence or reflection activity changes evidence history and aggregate progress at most once.
- **SC-005**: A user can inspect the current learner state, its supporting approved evidence, effective controls, progress, effort, and deferred activities in one bounded read operation per view.
- **SC-006**: No test fixture containing unapproved candidate content is accepted into learner evidence, control state, period progress, or deferred activities.
- **SC-007**: AT-10 and AT-11 control scenarios pass without blocking ordinary host work or confusing target completion with fatigue, pause, or disable.
- **SC-008**: All functional requirements map to executable unit or integration tasks, including the stated negative paths and real upstream/downstream contract handoffs.
- **SC-009**: Every valid threshold configuration produces deterministic monotonic state selection, while zero, negative, decreasing, and autonomous-below-two configurations are rejected and no numeric configuration bypasses a state-specific safeguard.

## Assumptions

- The upstream consent component supplies content-bound, session-bound, one-use approval and receipt semantics for every durable learner or control mutation.
- The upstream state owner supplies the shared SQLite connection and migration mechanism; this component specifies learner/control schema requirements and integration tasks but does not own `src/expertiseos/state/sqlite.py` concurrently.
- The retrieval component supplies approved knowledge results, versions, conflicts, provenance, and exclusion-aware retrieval hooks; learner state never treats retrieval as evidence.
- Host adapters supply trusted session and task references and enforce exclusions before source content reaches candidate detection.
- Product integration owns the shared behavioral skill and public service/MCP wiring, including presentation of optional reflection and deferred activities.
- Supported alternate rest duration units and validation bounds follow the upstream control API contract; unsupported values fail explicitly rather than silently changing defaults.

## Out of Scope

- Approval-gate implementation, canonical knowledge storage, Basic Memory mapping, retrieval ranking, or host event parsing.
- Shared `skill/SKILL.md`, service, MCP, onboarding, and host-specific UI or prompt wiring.
- Autonomous tutoring, background notifications, transcript harvesting, or always-running work.
- Psychometric scoring, global seniority, automatic decay, automatic deletion, or inferred mastery from model output.
- A general scheduler, workflow engine, policy language, or speculative compatibility layer.
