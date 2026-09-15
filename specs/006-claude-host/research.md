# Research: Claude Code Host Adapter

**Intent**: Record implementation decisions while keeping external host support claims tied to reproducible C001 feasibility evidence.

## Host Version and Event Mapping

**Decision**: Consume the exact Claude Code version, operating system, registration mechanism, permission mode, lifecycle/user event names, session identity behavior, and limitations from C001's passed G0 evidence. The implementation must not select or claim another combination independently.

**Rationale**: Official documentation establishes plausibility, not complete event visibility or the authorization boundary needed for writes.

**Alternatives considered**: Assuming latest Claude Code, using undocumented internals, transcript polling, or declaring parity from documentation were rejected.

## Actual-User Decision Boundary

**Decision**: Treat only the G0-proven actual-user input event kind as eligible for decision matching. The adapter constructs a C001 `DecisionObservation`; C002 alone registers the one-use grant and performs commit validation.

**Rationale**: This preserves independent proof that the person acted and prevents model/tool content from becoming authorization.

**Alternatives considered**: Model flags, tool permission callbacks, prompt text classification, quoted responses, and direct host-to-backend writes were rejected.

## Deterministic Controls

**Decision**: Recognize only unambiguous Save/Skip controls and explicit final-content Edit forms deterministically. Ambiguous natural language receives no grant and must be clarified by the host interaction before a later user event can authorize a write.

**Rationale**: No second classifier or generative service is needed, and ambiguity fails closed for memory writes.

**Alternatives considered**: Broad regex approval inference and a standalone intent classifier were rejected as unsafe and unnecessary.

## Safe Checkpoint Normalization

**Decision**: Normalize explicit C001-proven atomic begin/end events with an integer depth when available. Otherwise use only the narrowest proven post-operation boundary and mark `can_observe_atomic_boundaries` and its limitation accurately.

**Rationale**: Conservative checkpoints avoid interrupting work without inventing a scheduler or universal event stream.

**Alternatives considered**: Timers, background polling, and per-event model analysis were rejected.

## Minimal Adapter State

**Decision**: Keep adapter state volatile and session-scoped: normalized session ID, atomic depth, comparison-due flag, active decision binding, last user-event reference, and capability facts. Session end clears it and asks C002 to expire proposal/grant state.

**Rationale**: These facts are enough for ordering and binding; recovery of unapproved candidates is forbidden.

**Alternatives considered**: Durable event journals, retry queues, transcript caches, and adapter-owned databases were rejected.

## Shared-Service Boundary

**Decision**: The adapter uses the shared local service surface for controls, exclusions, retrieval, proposal lifecycle, decisions, and commits. It never accesses Basic Memory or SQLite directly.

**Rationale**: One enforcement point prevents host-specific domain drift and preserves cross-host identity/version behavior.

**Alternatives considered**: Claude-specific storage clients and duplicated approval/control logic were rejected.

## Failure Semantics

**Decision**: Convert expertiseOS failures to explicit capability/degraded/no-memory-action outcomes while returning control to the host task. Only C002 status `committed` may be rendered as Saved.

**Rationale**: Ordinary work must continue, but authorization and durability failures must never be hidden.

**Alternatives considered**: Retrying with changed content, optimistic Saved messages, and task-wide failure propagation were rejected.

## Onboarding and Configuration

**Decision**: Use the public registration and uninstall mechanism proven by G0, modifying only expertiseOS-owned entries and preserving unrelated host configuration. Keep host-specific setup translation in `claude_code.py` for MVP.

**Rationale**: A separate framework adds no value for one host-specific registration path.

**Alternatives considered**: Replacing configuration wholesale, manual database/model setup, and a generic plugin installer abstraction were rejected.

## Evidence Gate

Before write-capable implementation can be accepted, integration must provide C001 evidence showing:

- exact Claude Code version and supported OS/permission mode;
- public install, activation, health-check, and uninstall steps;
- raw event mappings for session start/end, actual user input, and safe checkpoint or bounded operation end;
- session identity source or proven generated-session lifetime;
- model/tool/assistant output rejected as user input;
- exact Save observation authorizes once while a model-only attempt fails;
- service failure leaves the reference host task successful.

Missing evidence yields an explicit unsupported capability, never an inferred implementation default.
