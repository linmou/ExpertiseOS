# Data Model: Consent Core

**Intent**: Define the smallest host-neutral records and lifecycle invariants needed to enforce exact user-approved semantic writes.

## Enumerations

- `KnowledgeCategory`: `declarative`, `structural_procedural`, `conditional_boundary`, `causal_mechanistic`, `episodic_tacit_experiential`, `goal_metacognitive_normative`
- `KnowledgeSubject`: `domain`, `self`, `ai`
- `KnowledgeStatus`: `active`, `retired`
- `ContributionOrigin`: `user`, `assistant`, `joint`
- `RelationType`: `derived_from`, `supports`, `contradicts`, `explains`, `example_of`, `applies_when`, `depends_on`
- `CandidateState`: `detected`, `awaiting_checkpoint`, `awaiting_decision`, `approved`, `declined`, `expired`
- `PendingOperationKind`: `create`, `revise`, `relation`, `conflict_resolution`, `learning_evidence`, `retire`, `delete`, `control_change`
- `UserDecisionAction`: `save`, `edit`, `skip`, `confirm_change`
- `LearnerState`: `new`, `recognized`, `explained`, `applied`, `transferred`, `autonomous`

## KnowledgeObject

| Field | Rule |
|---|---|
| `id` | Stable, non-empty opaque ID. |
| `version` | Positive integer; semantic revision increments by one. |
| `content` | Non-blank exact approved content. |
| `categories` | Zero or more unique `KnowledgeCategory` values. |
| `subjects` | One or more unique `KnowledgeSubject` values. |
| `applicability_scope` | Optional approved scope. |
| `evidential_status` | Optional approved uncertainty/evidence status. |
| `status` | Active or retired; retirement is not deletion. |
| `source_refs` | Zero or more approved `SourceReference` values. |
| `contribution_origin` | User, assistant, or joint. |
| `created_at`, `updated_at` | Explicit UTC timestamps; update cannot precede create. |

Learner state is not a `KnowledgeObject` field in C002. C004 derives it separately
from approved evidence; no qualifying evidence resolves to `new`.

## SourceReference

| Field | Rule |
|---|---|
| `source_type` | `host_event`, `conversation`, `file`, `artifact`, `tool_result`, `user_reflection`, or compatible user reference. |
| `host`, `session_id`, `event_ref` | Optional bounded origin identity. |
| `artifact_locator` | Optional locator, never full unrelated source content. |
| `approved_excerpt` | Optional excerpt explicitly shown within approval scope. |
| `date`, `checksum` | Optional source metadata. |
| `accessibility_status` | Explicit current availability; unavailable sources are not reconstructed. |

## Relationship

| Field | Rule |
|---|---|
| `id` | Stable non-empty ID. |
| `source_id`, `target_id` | Stable existing knowledge IDs. |
| `source_version`, `target_version` | Optional bound versions when semantic correctness depends on them. |
| `type` | One supported `RelationType`. |
| `explanation` | Optional exact approved explanation. |
| `source_ref` | Optional approved provenance. |

Adding, removing, or changing a relationship is a semantic operation.

## PendingOperation

| Field | Rule |
|---|---|
| `proposal_id` | Unique within active volatile state. |
| `operation_id` | Canonical replay identity, fixed when the proposal is created and required to match at commit. |
| `session_id`, `adapter_id` | Immutable origin binding. |
| `kind` | One `PendingOperationKind`. |
| `state` | One `CandidateState`. |
| `payload` | Typed semantic payload held only in memory. |
| `content_digest` | Canonical digest of displayed semantic fields. |
| `expected_versions` | Stable object ID to expected positive version mapping. |
| `created_at` | Explicit UTC timestamp. |

### State Transitions

```text
detected -> awaiting_checkpoint -> awaiting_decision
awaiting_decision -> approved
detected | awaiting_checkpoint | awaiting_decision -> declined | expired
```

Terminal states never transition. Session end expires every unresolved candidate. An unrelated next user event expires `awaiting_decision` unless the adapter identifies it as that proposal's decision.

### Delegated Operation Payloads

`LearningEvidenceOperation`, `ControlChangeOperation`, and `DeleteOperation` are distinct frozen
wrappers around the exact displayed downstream value. They form the closed `DelegatedOperation`
union included in `OperationPayload`; they are excluded from the knowledge-only `MutationEffect`
union. C002 hashes and retains the value only in volatile proposal state. C004 and C007 retain
ownership of validation, persistence, and exact read-back for their respective values.

## DecisionGrant

| Field | Rule |
|---|---|
| `grant_id` | Unique volatile grant ID. |
| `proposal_id`, `session_id`, `adapter_id` | Exact immutable proposal origin binding. |
| `action` | Exact user decision. |
| `content_digest` | Must equal the current displayed proposal digest. |
| `user_event_ref` | Opaque reference to the validated actual user event. |
| `created_at` | Explicit UTC timestamp. |
| `consumed_at` | Explicit optional timestamp supplied as `None` at construction; set once only after full commit success. |

One grant resolves one proposal. Unused grants expire with the proposal/session and have no durable serialization.

## AuthorizedOperation

| Field | Rule |
|---|---|
| `grant_id`, `proposal_id` | Exact volatile grant and proposal binding. |
| `operation_id` | Canonical replay identity validated during preparation. |
| `session_id`, `adapter_id`, `user_event_ref` | Exact actual-user origin binding. |
| `kind`, `payload`, `content_digest` | Closed delegated kind and exact canonical content binding. |
| `expected_versions` | Exact versions checked against trusted producer state. |
| `existing_receipt` | Explicit `None` for pending work or the exact receipt for completed replay. |

The service keeps a matching volatile prepared authorization. The record alone is not proof of a
completed mutation and cannot create a receipt until trusted composition has executed and read back
the downstream state.

## ApprovalReceipt

| Field | Rule |
|---|---|
| `operation_id` | Canonical `operation_id` used for bounded replay and receipt identity. |
| `proposal_id` | Approved proposal identity. |
| `operation_kind` | Exact semantic operation. |
| `object_ids_versions` | Canonically serialized affected stable IDs and versions: resulting stored versions, or the approved pre-delete versions for deleted objects. |
| `content_digest` | Digest validated by the gate. |
| `user_event_ref` | Actual user-event reference from the consumed grant. |
| `adapter_id` | Origin adapter identity. |
| `created_at` | UTC completion timestamp. |

Receipts contain no proposal payload, full prompt, or unused authorization. A repeated `operation_id` is accepted only when every stored receipt field matches the completed operation.

## Volatile Stores

- `CandidateStore`: active proposals keyed by proposal ID with session indexes and same-session decline fingerprints.
- `DecisionGrantStore`: unconsumed/consumed grants keyed by grant ID and indexed to the bound proposal.

Neither store exposes a durable serializer or receives a SQLite connection.

## Persistent State

`approval_receipts` is the only C002 table. See [state-schema.md](contracts/state-schema.md). Learner evidence, controls, deferred learning, and installation tables are owned by later components and must be added through forward-only SQLite migrations without changing receipt semantics.
