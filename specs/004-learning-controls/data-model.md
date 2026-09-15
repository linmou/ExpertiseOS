# Data Model: Learner Evidence and Learning Controls

**Intent**: Define minimal logical records and invariants for deterministic learning state and user controls.

## LearnerEvidence

| Field | Meaning | Constraint |
|---|---|---|
| `id` | Stable evidence event ID and idempotency key | Required, unique |
| `knowledge_id` | Approved object ID | Required, must resolve through C003 |
| `knowledge_version` | Version the evidence concerns | Required, positive |
| `task_ref` | Stable task/activity reference | Required for applied-or-higher evidence |
| `session_id` | Trusted originating host session | Required for independence checks |
| `criterion` | Observable performance criterion | Required, nonblank |
| `outcome` | `pass`, `partial`, `fail`, or `insufficient_evidence` | Required |
| `assistance_level` | Known degree of assistance | Required; unknown cannot prove independence |
| `scope` | Applicability boundary | Required, comparable with requested mastery scope |
| `user_contribution` | Approved excerpt or summary of attributable contribution | Required for advancement, bounded |
| `proposed_state` | Proposed interpretation | Required |
| `approved_state` | User-approved interpretation | Required for advancement |
| `is_meaningful_transfer` | Materially different case with boundary handling | Required boolean |
| `approval_receipt_id` | C002 receipt | Required before persistence |
| `created_at` | Event time | Required |

Self-report, when carried by an upstream record, is never interpreted as demonstrated evidence.
Only `pass` contributes toward advancement; all other outcomes remain stored and inspectable with zero contribution.

## LearnerStateSummary

| Field | Meaning |
|---|---|
| `knowledge_id` | Approved object ID |
| `knowledge_version` | Exact summarized version |
| `scope` | Exact summarized applicability boundary |
| `state` | One of the six learner states |
| `supporting_evidence_ids` | Approved applicable evidence used |
| `excluded_evidence_ids` | Retained but inapplicable or nonqualifying evidence |
| `unmet_autonomy_conditions` | Deterministic reasons autonomous was withheld |
| `calculated_at` | Inspection time, not an independent mastery event |

The summary is regenerated from evidence initially. It is not a separate source of truth.

## AdvancementThresholds

| Field | Meaning | Constraint |
|---|---|---|
| `recognized_passes` | Pass count required for recognized | Positive integer |
| `explained_passes` | Pass count required for explained | Positive integer, at least prior threshold |
| `applied_passes` | Pass count required for applied | Positive integer, at least prior threshold |
| `transferred_passes` | Pass count required for transferred | Positive integer, at least prior threshold |
| `autonomous_passes` | Independent pass count required for autonomous | Integer at least 2 and at least prior threshold |

The explicit initial values are `1, 1, 1, 1, 2`. Counts do not replace state-specific evidence meanings. Autonomous also requires distinct tasks, separate sessions, transfer, contradiction clearance, and explicit agreement.

## ControlSettings

| Field | Meaning | Constraint |
|---|---|---|
| `enabled` | Full expertiseOS enablement | Required |
| `learning_paused` | Explicit pause | Required |
| `pause_until` | Optional user-selected expiry | Nullable |
| `target_period` | `daily` or `weekly` | Required |
| `reflection_target` | Qualifying activities per period | Positive integer |
| `effort_limit` | Maximum effort per block | Positive decimal |
| `rest_interval_minutes` | Fatigue rest duration | Positive integer |
| `fatigue_rest_until` | Active rest end | Nullable |
| `timezone_id` | Local device timezone used for period keys | Required |
| `advancement_thresholds` | Versioned user-owned pass thresholds | Required |
| `version` | Optimistic settings version | Positive |

Defaults are supplied explicitly when settings are instantiated: daily, 1 reflection, 6 effort units, 60 minutes rest, and advancement thresholds `1, 1, 1, 1, 2`. The weekly preset explicitly supplies weekly and 3 reflections.

## PeriodProgress

| Field | Meaning | Constraint |
|---|---|---|
| `period_key` | Daily date or weekly year/week in settings timezone | Required |
| `reflection_count` | Unique qualifying activities | Nonnegative |
| `effort_units` | Sum of unique response classifications | Nonnegative |
| `reflection_event_ids` | Idempotency set represented by state owner | Unique per event |
| `effort_event_ids` | Idempotency set represented by state owner | Unique per event |

## ScopeExclusion

| Field | Meaning | Constraint |
|---|---|---|
| `id` | Stable exclusion ID | Required |
| `kind` | `source`, `path`, or `session` | Required |
| `value` | Exact user-selected scope value | Required, nonblank |
| `created_at` | Approval completion time | Required |
| `approval_receipt_id` | C002 receipt | Required |

Matching is literal/canonical path-or-ID comparison. No policy expression language is introduced.

## DeferredActivity

| Field | Meaning | Constraint |
|---|---|---|
| `id` | Stable activity ID | Required, unique |
| `knowledge_refs` | One or more approved ID/version pairs | Required, nonempty |
| `activity_type` | Bounded activity kind | Required |
| `created_at` | Approval completion time | Required |
| `status` | `pending` or `removed` | Required |
| `approval_receipt_id` | C002 receipt for create/remove | Required |

No free-form candidate claim or prompt field exists.

## ControlResolution

| Field | Meaning |
|---|---|
| `reason` | `disabled`, `paused`, `fatigue_rest`, `target_satisfied`, or `active` |
| `observe` | Whether expertiseOS may observe eligible host context |
| `prompt_collection` | Whether candidate detection/proposals may be proactive |
| `proactive_exercises` | Whether learning exercises may be offered |
| `approved_recall` | Whether approved knowledge recall is available |
| `expires_at` | Optional pause/rest boundary |

## State Transitions

- Evidence proposal -> approved persistence only through C002 -> summary recalculation on read.
- Explicit fatigue -> expire unresolved candidates through the upstream lifecycle owner -> set rest end -> preserve target progress.
- Period rollover -> start a new progress record -> preserve pause/rest/settings/exclusions.
- Deferred pending -> removed only by an approved explicit removal; it is never auto-completed in background.
- Control settings changes use expected version and exact approval; stale changes fail rather than overwrite.
