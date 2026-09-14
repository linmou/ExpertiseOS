# G0 Contract Data Model

**Intent**: Define only values crossing feasibility contracts; later components own product lifecycle entities.

## HostCapability

Required fields: `name`, `available`, `evidence_ref`, and `limitation`.

- `available=true` requires a non-empty evidence reference.
- Missing authorization capability cannot be inferred from another capability.

## HostEvent

Required fields: `event_id`, `adapter_id`, `session_id`, `kind`, `occurred_at`, `user_input_ref`, and `action`.

- `kind` is `session_start`, `user_input`, `atomic_begin`, `atomic_end`, `checkpoint`, or `session_end`.
- Assistant, model, and tool output never use `user_input`.
- First event is session start; no event follows session end.
- A checkpoint inside an atomic operation is ineligible for prompting.
- Unrelated raw prompts are not retained to prove authorization.

## HostSession

Required fields: `adapter_id`, `session_id`, `capabilities`, `active_atomic_operations`, and `state` (`active` or `ended`).

Transitions: session start activates; atomic begin/end adjusts operation depth; session end terminates.

## ApprovedKnowledgeInput

Required fields: `content`, `content_digest`, `categories`, `subjects`, `applicability_scope`, `evidential_status`, `source_refs`, and `contribution_origin`.

- It contains no approval boolean.
- It contains no `operation_id`; command identity is runtime metadata supplied separately to mutation methods.
- Every field is explicitly supplied; constructors provide no defaults.
- Fake backend rejects unapproved test wrappers before retaining data.

## Mutation Command

Every create, update, relationship, retire, and delete call receives `operation_id` as its sole idempotency identity, separate from approved semantic values. The normalized command input comprises the method, target identity, expected version or versions, and semantic payload.

- Repeating the same `operation_id` with identical normalized command input returns the originally recorded result without another semantic mutation.
- Reusing the same `operation_id` with any different normalized command input returns a typed idempotency conflict.
- A new `operation_id` represents a new command and remains subject to ordinary existence and expected-version checks.

## KnowledgeRecord

Required fields: `id`, `version`, all approved knowledge fields, `status`, `relationships`, `created_at`, and `updated_at`.

- Identity is stable and version is monotonic.
- Update and retire require matching expected versions.
- `get` returns the current active record by default, supports an exact retained historical version, and includes retired records only when explicitly requested.
- Batched current-version lookup returns identity-to-version mappings without semantic content.
- Search defaults to active records.

## RelationshipInput

Required fields: `source_id`, `source_version`, `target_id`, `target_version`, `type`, `explanation`, and `source_ref`.

- Endpoints resolve under the backend contract.
- The caller has already authorized the operation; no approval flag exists.

## SearchQuery and SearchResult

`SearchQuery` requires query text, positive limit, and an explicit optional scope value. `SearchResult` requires identity/version, bounded excerpt, provenance, relationship/conflict summaries, match mode, and index health.

- Results never exceed the limit.
- Retrieved text is untrusted data.
- Match mode distinguishes local semantic search and keyword fallback.

## BackendHealth

Required fields: canonical-store state, index state, search mode, and bounded diagnostic details without candidate or unrelated prompt content.

## FeasibilityEvidence

Required fields: `evidence_id`, `component`, `version_or_commit`, `operating_system`, `capability`, `command_or_manual_steps`, `fixture_ref`, `result`, `exit_status`, `captured_at`, and `limitation`.

- Support requires a passed result and complete environment/fixture metadata.
- Limited/failed results state the capability effect.
- Not-run evidence never supports a claim.

## Excluded Product Entities

Candidate, PendingOperation, DecisionGrant, ApprovalReceipt, LearnerEvidence, mastery/control state, and durable service state are not implemented here.
