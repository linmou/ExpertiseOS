# Contract: Claude Code Host Adapter

**Intent**: Define the C006 producer/consumer boundary without changing C001-C004 semantics.

## Inputs

The adapter accepts only:

- a G0-supported Claude event plus the exact environment identity used to select capabilities;
- C001 host contract values and active `DecisionBinding`;
- C002 service operations for proposal lifecycle, decision registration, and commit;
- C003 service-facing bounded retrieval;
- C004 control resolution and scope-exclusion result.

Raw Claude SDK/hook types do not cross this module boundary.

## Normalization

```text
normalize(raw_event, session) -> HostEvent | UnsupportedEvent | InvalidEvent
```

Required mappings are session start, actual user input, atomic begin, atomic end, safe checkpoint, and session end where proven. If a host capability is unavailable, the adapter emits no fabricated normalized event and reports the limitation.

## Checkpoint Eligibility

```text
checkpoint_eligible(session, control_resolution, excluded) -> boolean
```

Eligibility requires an active session, `atomic_depth == 0`, a supported checkpoint, no applicable exclusion, and the specific C004 permission needed for the proposed observation, collection prompt, exercise, or recall. The adapter does not recreate control precedence.

## Decision Observation

```text
register_decision_if_unambiguous(
  event: HostEvent,
  binding: DecisionBinding,
) -> DecisionObservation
```

A match requires:

- G0-proven actual-user origin;
- one active proposal;
- identical adapter and session identities;
- an allowed unambiguous action;
- the current displayed digest and expected versions;
- a fresh opaque event reference.

The observation does not authorize a write. C002 verifies and registers a one-use grant. An Edit with final content returns a revision-required outcome for re-display and later Save. Ambiguous or unrelated input returns no grant request; unrelated input also requests expiry of the active proposal.

## Direct Save

```text
actual_user_direct_save(event, immediate_reference) -> matching proposal/decision inputs or requires later proposal
```

The exact function name and values follow the reconciled C001/C002 service boundary. This path is allowed only when exact material is deterministically identified by the actual user event and immediate active reference. It cannot add inferred categories, relations, provenance excerpts, or claims. Otherwise a normal proposal must be displayed and approved later.

## Service Boundary

C001 lifecycle callbacks retain their fixed return types. Adapter service-call handling MUST preserve the host's task result independently of memory status. Only C002 `committed` maps to Saved. Rejected, conflict, failed, incomplete, unavailable, timeout, and malformed responses return control to the host while reporting no successful write; no additional host-neutral result type is introduced by C006.

## Capability Rules

The adapter reports each capability independently:

```text
can_read
can_search
can_validate_user_decisions
can_write
can_observe_atomic_boundaries
can_auto_activate
```

Availability requires passed evidence for the exact version/OS/permission mode. `can_write` is false unless decision validation is passed and the guarded service is reachable/healthy for writes.

## Integration Handoff Tests

1. C001 sanitized actual-user fixture becomes one matching observation; assistant/tool/model variants do not.
2. The matching observation reaches the real C002 registration/commit path and commits once; changed digest/version/session/adapter fixtures do not.
3. C004 disabled, paused, fatigue, target-satisfied, active, and excluded fixtures drive observation/prompt/recall behavior exactly as resolved upstream.
4. A real C003 approved retrieval response reaches Claude-facing rendering with original ID/version, bounds, provenance/conflict/health data, and `untrusted_data` label.
5. A forced service failure returns host continuation and no Saved result.
6. Session end invokes C002 expiry and clears adapter volatile state without durable candidate content.
7. Pinned live-host evidence proves activation, safe checkpoint, user capture, failure-open behavior, expiry, and capability truthfulness.
