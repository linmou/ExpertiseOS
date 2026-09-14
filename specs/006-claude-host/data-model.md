# Data Model: Claude Code Host Adapter

**Intent**: Define only Claude-owned volatile translation values and evidence records; reuse upstream domain values unchanged.

## ClaudeHostSession

| Field | Rule |
|---|---|
| `adapter_id` | Required constant identity for the Claude adapter. |
| `session_id` | Required host-provided identity or G0-approved generated identity scoped to one live host session. |
| `capabilities` | Required tuple of C001 `HostCapability` values for the exact running environment. |
| `atomic_depth` | Required nonnegative integer; a checkpoint is ineligible while positive. |
| `comparison_due` | Required boolean; does not itself authorize analysis or prompting. |
| `active_binding` | Required explicit optional C001 `DecisionBinding`, supplied as a value or `None` at construction. |
| `last_user_event_ref` | Required explicit optional opaque actual-user event reference, supplied as a value or `None`. |
| `state` | Required `active` or `ended`. |

Every constructor field is required. No dataclass field receives a definition-time default.

## ClaudeRawEvent

| Field | Rule |
|---|---|
| `event_name` | One public event name proven for the pinned host version. |
| `event_ref` | Required opaque event identity; never synthesized from content. |
| `session_ref` | Required host session reference when exposed. |
| `occurred_at` | Required explicit UTC timestamp. |
| `payload` | Bounded transient supported fields needed for mapping; unrelated prompt/source text is not retained. |
| `origin_kind` | Required host-proven origin class distinguishing user, assistant, tool, model, and lifecycle events. |

The raw value exists only during event handling or inside sanitized test fixtures. It has no persistence API.

## ClaudeCapabilityEvidence

| Field | Rule |
|---|---|
| `host_version` | Exact tested Claude Code version. |
| `operating_system` | Exact tested OS/version. |
| `permission_mode` | Exact tested permission/sandbox mode. |
| `registration_mechanism` | Supported public activation path. |
| `capability_name` | One of C001's six capability names. |
| `event_names` | Exact public events proving the capability, possibly empty for unavailable capabilities. |
| `fixture_ref` | Reproducible sanitized fixture or manual evidence reference. |
| `result` | `passed`, `limited`, `failed`, or `not_run`. |
| `limitation` | Required explicit text, including an empty string when passed without a known limit. |

Only `passed` evidence can produce an available capability. `can_write` additionally requires passed `can_validate_user_decisions` evidence.

## Upstream Values Reused Unchanged

- C001: `HostEvent`, `HostCapability`, `DecisionBinding`, and `DecisionObservation`.
- C002: `PendingOperation`, `DecisionGrant`, proposal expiry, registration, and `CommitResult`.
- C003: bounded `RetrievalResponse` and its explicit health/trust fields.
- C004: `ControlResolution` and literal `ScopeExclusion` matching.

The adapter adds no wrapper domain model around these values.

## State Transitions

```text
not_started -> supported session_start -> active
active -> atomic_begin -> active with atomic_depth + 1
active with atomic_depth > 0 -> atomic_end -> active with atomic_depth - 1
active with atomic_depth = 0 -> supported checkpoint + allowed controls -> eligible checkpoint
active + proposal displayed -> active with exact DecisionBinding
matching actual user Save -> DecisionObservation(match) -> C002 registration
actual user final-content Edit -> revised proposal displayed -> new DecisionBinding
Skip | unrelated next user event | session_end -> C002 expire/decline -> no active binding
active -> session_end -> ended; all adapter volatile state cleared
```

Events before start, after end, with wrong identity, or with unsupported names yield typed rejection/no-op outcomes and no shared-state mutation.

## Persistence Boundary

The adapter persists no session, candidate, raw event, decision binding, prompt, query, or retrieved content. Sanitized versioned test fixtures contain event shapes and marker-safe test values only. C002/C003/C004 own all allowed durable state.
