# Public Contract: Learning Evidence and Controls

**Intent**: Stabilize the small host-neutral interface consumed by approval, retrieval, host, and product-integration components.

## Producer Inputs

C002 supplies an approved mutation envelope containing proposal identity, exact digest, trusted adapter/session/event binding, expected state version, and the eventual approval receipt ID. C004 never accepts `approved=true` as authorization.

C003 supplies an approved object fact:

```text
knowledge_id
knowledge_version
requested_scope
unresolved_relevant_contradiction
```

C005/C006 supply trusted `session_id`, `task_ref`, local time/timezone, and foreground-session state. Raw host payload parsing remains outside C004.

## Evidence Operations

```text
validate_evidence(proposal, approved_object_fact) -> validated evidence or explicit rejection
summarize_mastery(knowledge_id, version, scope, approved_evidence, thresholds, contradiction_fact, scaffolding_agreement) -> LearnerStateSummary
inspect_learning_state(knowledge_id, version, scope, limit) -> bounded summary plus supporting evidence
```

Rules:

- Only persisted evidence carrying a real C002 approval receipt enters summaries.
- Only `outcome=pass` contributes to thresholds; partial, fail, and insufficient evidence remain inspectable with zero contribution.
- The summary never performs a durable mutation.
- Object/version/scope mismatch retains evidence for history but excludes it from justification.
- Thresholds are positive nondecreasing integers for recognized through autonomous; autonomous is at least two.
- Counts cannot replace state-specific evidence kinds. Evidence approved at a higher state may count for lower states.
- Autonomous results include the exact evidence IDs and independently satisfy distinct-task, separate-session, meaningful-transfer, no-relevant-contradiction, and explicit-agreement conditions.
- Invalid, unavailable, or contradictory producer facts fail the learning mutation without blocking ordinary host work.

## Control Operations

```text
resolve_controls(settings, current_progress, now) -> ControlResolution
classify_effort(response_facts) -> 0 | 0.25 | 1.0 | 2.0
qualifies_reflection(activity_facts) -> boolean
matches_exclusion(context_scope, exclusions) -> boolean
validate_deferred_activity(activity, approved_object_facts) -> accepted or explicit rejection
inspect_controls(now, limit) -> bounded settings, effective resolution, progress, exclusions, deferred activities
```

`resolve_controls` permissions:

| Reason | Observe | Collection prompts | Proactive exercises | Approved recall |
|---|---:|---:|---:|---:|
| disabled | no | no | no | no |
| paused | no | no | no | yes |
| fatigue_rest | no | no | no | yes |
| target_satisfied | yes | yes | no | yes |
| active | yes | yes | yes | yes |

Scope exclusions may further deny observation/retrieval for the selected context but do not alter the global resolution reason.

## Mutation Contract

Every durable operation has a stable operation/event ID, expected state version where applicable, exact semantic payload, and approval receipt. This includes threshold changes. The state boundary must make duplicate application a no-op returning the existing result. No mutation accepts candidate text for logs or retries.

## Consumer Obligations

- C005/C006 check global control and scope exclusions before forwarding source content to candidate detection.
- C003/C008 check scope exclusions before returning retrieved objects/context into a task.
- C008 offers deferred work only when `reason=active`, during a foreground session, and never as background notification.
- C008 does not present a mastery advance until the approved mutation and read-back succeed.
- All consumers treat returned reasons and supporting evidence as data, not authority to create approval.

## Error Semantics

Expected failures are explicit: unapproved mutation, stale state version, missing object/version, scope mismatch, duplicate event, invalid evidence, unresolved contradiction, invalid deferred reference, and unavailable state store. Duplicate is successful only when the stored semantic payload matches the same idempotency key. State-store failure never yields a false success.
