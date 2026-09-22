# Contract: Codex Adapter Boundary

## Upstream Inputs

- Promoted `HostAdapter` normalized event and capability types from C001.
- Proposal display/binding, actual-user decision registration, decline/expiry, and session cleanup operations from C002.
- Bounded approved retrieval and explicit degraded status from C003.
- Resolved enabled/pause/fatigue/target state and source/path/session exclusions from C004.
- Immutable G0 evidence satisfying [g0-evidence.md](g0-evidence.md).

## Adapter Outputs

The adapter emits normalized session-start, actual-user, atomic-start, atomic-finish, safe-checkpoint, and session-end facts supported by the promoted HostAdapter contract. It exposes an evidence-backed capability snapshot at session start.

## Required Invariants

1. Raw Codex payload types do not escape `hosts/codex.py`.
2. Only the G0-verified actual-user source can reach decision registration.
3. Model output, tool output, generic permission, quoted text, and synthesized events cannot reach that path.
4. The adapter supplies upstream binding fields unchanged and never creates a durable write itself.
5. No safe checkpoint is emitted while a supported atomic operation is incomplete.
6. Disabled or excluded content is rejected before observation/retrieval forwarding.
7. Session end invokes upstream expiry/cleanup and removes local volatile state.
8. Adapter/service exceptions are contained so ordinary Codex work continues; failed writes never produce success.
9. A capability is true only when the exact session environment matches passing G0 evidence.

## Decision Matrix for One Active Proposal

| Actual-user input | Adapter action |
|---|---|
| Clear Save | Register matching Save decision once |
| Clear Skip/cancel | Decline or expire; register no write decision |
| Edit with final content | Ask upstream to replace/re-digest and re-display; await a later matching decision |
| Edit without final content | Register no decision; permit host revision and re-display |
| Unrelated message | Expire proposal; register no decision |
| Ambiguous or quoted response | Register no decision; request clarification if appropriate |
| Multiple active proposals | Register no generic decision; require itemized disambiguation |

## Failure Semantics

- Unsupported/unverified environment: expose only proven capabilities; write remains false without actual-user proof.
- Service/search unavailable: suppress expertiseOS side action, preserve host task, expose degradation when possible.
- Upstream mutation rejected or fails: never render a Saved result from the adapter.
- Unknown/unbalanced atomic state: treat checkpoint as unsafe.

## Downstream Handoff to C008

C008 may consume the normalized adapter and its evidence fixtures for shared behavior and cross-host acceptance. It must not bypass the upstream approval service or reinterpret raw Codex payloads.
