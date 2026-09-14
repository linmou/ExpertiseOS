# Data Model: Codex Host Adapter

All component state is volatile unless G0 proves that minimal installation registration metadata must be durable. Candidate content, decision grants, knowledge, learner evidence, and controls belong to upstream owners.

## CodexSessionState

| Field | Meaning | Validation |
|---|---|---|
| `adapter_id` | Stable Codex adapter identifier | Matches promoted HostAdapter identity |
| `session_id` | Current host-scoped session identity | Non-empty; never reused across ended sessions |
| `capabilities` | Immutable session-start capability snapshot | Each true value cites matching G0 evidence |
| `atomic_depth` | Supported in-flight atomic nesting count, or promoted equivalent | Non-negative; checkpoint unsafe above zero |
| `comparison_due` | Whether a later eligible checkpoint should request comparison | Boolean; does not itself run semantic analysis |
| `active_proposal_id` | Single active upstream proposal reference | Zero or one unless explicit itemized flow is added by requirement |
| `active_content_digest` | Exact digest shown for active proposal | Present only with active proposal |
| `allowed_actions` | Actions displayed for the binding | Subset of Save/Edit/Skip supported by upstream contract |
| `expected_versions` | Versions displayed and bound upstream | Opaque normalized mapping; never recomputed by adapter |
| `last_user_event_ref` | Reference to most recent verified actual-user event | Reference only; unrelated prompt text is not retained |

### Lifecycle

```text
not_started -> active -> ended
```

- Activation creates `active` state after support/capability checks.
- Atomic start/end modify only the safe-checkpoint state.
- Proposal display sets one active binding; Save/Edit/Skip/unrelated message resolves or replaces it through upstream APIs.
- Session end expires upstream candidate/grant state and destroys all local session state.

## NormalizedHostEvent

| Field | Meaning | Validation |
|---|---|---|
| `kind` | session start, actual user, atomic start, atomic finish, checkpoint, or session end | Must map from a G0-verified Codex event source |
| `adapter_id` | Producing adapter | Must equal current adapter |
| `session_id` | Originating session | Must equal active session |
| `event_ref` | Minimal stable host event reference | Required for actual-user decisions |
| `payload` | Contract-specific bounded event data | Excludes hidden reasoning and unrelated transcript content |

## CapabilitySnapshot

Flags: `can_read`, `can_search`, `can_validate_user_decisions`, `can_write`, `can_observe_atomic_boundaries`, `can_auto_activate`.

Every true flag maps to an exact tested Codex version, OS, installation surface, permission mode, fixture, and evidence result. `can_write` additionally requires `can_validate_user_decisions` and compatible upstream approval service health.

## ActiveProposalBinding

This is a volatile reference to an upstream proposal, not a duplicate candidate record. It binds proposal, adapter, session, displayed digest, allowed actions, expected versions, and the displayed event/checkpoint. The adapter cannot mutate semantic payload fields or commit directly.

## InstallationRegistration

Only the minimal information necessary to reverse the G0-proven supported registration may persist. It must preserve unrelated host configuration, contain no candidate content, and record onboarding consent/capability evidence through upstream installation state when required.
