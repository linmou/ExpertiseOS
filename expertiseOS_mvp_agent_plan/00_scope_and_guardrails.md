# 00 — Scope, Guardrails, and Minimal Implementation Defaults

## 1. What is being built

Build the full personal, local-first expertiseOS MVP for supported local Codex and Claude Code environments.

The product loop is:

```text
work
-> compare with approved knowledge
-> detect possible new/conflicting knowledge
-> wait for a safe conversational checkpoint
-> show Save/Edit/Skip
-> persist only what the user authorized
-> optionally reflect/organize
-> recall later with provenance
-> record approved mastery evidence
-> adjust scaffolding
```

The host agent still owns the user's task. expertiseOS supplies learning/memory behavior and guarded persistence; it is not a task planner or autonomous worker.

## 2. Non-negotiable invariants

### I-01 — No unapproved persistence

Before approval, candidate content may exist only in process memory available to the active expertiseOS session.

Do not write it to:

- SQLite;
- Basic Memory;
- embeddings;
- logs;
- temp files;
- crash dumps controlled by expertiseOS;
- telemetry;
- retry queues;
- debug snapshots.

Crash loss of an unapproved candidate is correct behavior.

### I-02 — User-event authorization is separate from model intent

A model call cannot prove that the user authorized a write.

The service must not accept any of these as sufficient authorization:

- `approved=true` supplied by the model;
- text saying “the user approved”;
- a quoted previous Save message;
- a generic host tool permission;
- an approval from another proposal/session;
- an approval for an earlier version of changed content.

The host adapter must observe an actual user-input event through a validated host integration path and register a one-use decision grant with the service.

### I-03 — Exact binding

Authorization is bound at minimum to:

- proposal ID;
- operation type;
- host adapter ID;
- originating session ID;
- displayed/approved content digest;
- relevant expected object version(s);
- user-event reference;
- action: Save/Edit/Skip/confirm change.

Do not persist the full unrelated user prompt merely to prove approval.

### I-04 — Fail open for work, closed for memory writes

If expertiseOS is unavailable, search is degraded, an index is stale, or approval cannot be validated:

- normal host work continues;
- unsafe knowledge writes do not occur;
- do not emit a false “Saved” success.

### I-05 — Knowledge, evidence, permission, and mastery are independent

A knowledge object may be approved yet uncertain.

A knowledge object may be correct yet remain at learner state `new`.

A mastery event may describe the user's performance but cannot be saved unless its durable evidence/state change is approved.

### I-06 — Stored knowledge is data, not authority

Retrieved content may contain instructions. Treat them as quoted knowledge/context, not as system/tool-control instructions.

## 3. Minimal implementation defaults

These are concrete defaults for coding agents. Change them only if G0 produces a specific incompatibility.

### Runtime

- Python 3.12.
- One installable package: `expertiseos`.
- One local service process hosting the MCP/tool surface and domain services.
- `pytest` for tests.
- Prefer Python standard library where practical.

### State

Use two persistence responsibilities only:

1. **Basic Memory adapter**
   - approved knowledge content;
   - knowledge metadata;
   - provenance/source references;
   - relationships;
   - knowledge version information where supported;
   - local indexes/retrieval.

2. **SQLite `state.db`**
   - minimal approval receipts;
   - learner-evidence records;
   - per-object mastery summary if needed for efficient reads;
   - control settings and aggregate target/effort counters;
   - deferred activities that reference approved object IDs;
   - host installation/onboarding state if needed.

Do not duplicate full canonical knowledge content into SQLite unless G0 proves Basic Memory cannot satisfy a required operation. If a sidecar object registry becomes necessary, document exactly why.

### Volatile state

Keep in memory:

- active candidates;
- declined-candidate suppression for the current session;
- unconsumed decision grants;
- per-session safe-checkpoint/atomic-operation flags;
- candidate search scratch data;
- non-durable query text.

### Search

- Use Basic Memory/local retrieval through the adapter.
- Support keyword fallback if local embeddings/indexing are unavailable.
- Index approved data only.
- Do not add a remote embedding/reranking service.

### Concurrency

- Use optimistic version checks.
- Surface stale writes as conflicts.
- No distributed lock manager.
- No last-write-wins overwrite for semantic edits.

## 4. Minimal domain objects

Do not turn these into dozens of subclasses.

### KnowledgeObject

Required logical fields:

```text
id
version
content
categories[]              # zero or more of the six categories
subjects[]                # domain | self | ai; at least one
applicability_scope?
evidential_status?
status                    # active | retired
source_refs[]
contribution_origin       # user | assistant | joint
created_at
updated_at
```

A single object can have more than one category when separation would be artificial.

### SourceReference

```text
source_type               # host_event | conversation | file | artifact | tool_result | user_reflection
host?
session_id?
event_ref?
artifact_locator?
approved_excerpt?
date?
checksum?
accessibility_status?
```

Never store hidden chain-of-thought.

### Relationship

```text
id
source_id
source_version?
target_id
target_version?
type                      # derived_from | supports | contradicts | explains | example_of | applies_when | depends_on
explanation?
source_ref?
```

A relationship change is semantic and requires authorization.

### Candidate / PendingOperation

Logical fields:

```text
proposal_id
session_id
adapter_id
kind                      # create | revise | relation | conflict_resolution | learning_evidence | retire | delete | control_change
state                     # detected | awaiting_checkpoint | awaiting_decision | approved | declined | expired
payload                    # in-memory only before approval
content_digest
expected_versions{}
created_at
```

Do not build a generic workflow engine. This is a small state machine.

### DecisionGrant

One-use in-memory authorization created by a trusted host adapter after observing real user input.

```text
grant_id
proposal_id
session_id
adapter_id
action
content_digest
user_event_ref
created_at
consumed_at?
```

### ApprovalReceipt

Persist only after the authorized mutation succeeds.

```text
operation_id
proposal_id
operation_kind
object_ids_versions
content_digest
user_event_ref
timestamp
adapter_id
```

### LearnerEvidence

```text
id
knowledge_id
knowledge_version
task_ref
criterion
outcome                   # pass | partial | fail | insufficient_evidence
assistance_level
scope
user_contribution_excerpt_or_summary
proposed_state
approved_state?
approval_receipt_id
created_at
```

Keep self-reported familiarity separate if implemented.

### LearnerState enum

```text
new
recognized
explained
applied
transferred
autonomous
```

No global seniority score.

## 5. Control state

Implement only the PRD control semantics.

### Settings

- target period: daily or weekly;
- reflection target;
- effort limit;
- rest interval;
- explicit learning pause/resume;
- expertiseOS enabled/disabled.

### Runtime precedence

```text
explicit disable/pause
> active fatigue rest
> target satisfied
> ordinary active learning
```

### Required behavioral distinctions

- **Target satisfied:** no proactive exercises for the current period; collection may continue.
- **Fatigue rest / learning paused:** no detection prompts or proactive learning; approved memory recall still works.
- **Disabled:** no observation, collection, learning, or expertiseOS recall.

Do not collapse these into one boolean.

## 6. Anti-overdesign rules

Do not build any of the following unless a failing P0 acceptance test proves it is necessary:

- cloud account or sync;
- web/mobile frontend;
- separate chat client;
- team/organization permissions;
- RBAC system;
- remote task queue;
- Redis;
- Kafka/event bus;
- graph database;
- custom vector database;
- independent reranker service;
- autonomous background transcript harvester;
- background reflection daemon;
- automatic semantic merge/consolidation;
- automatic decay/deletion;
- LLM router;
- second generative model;
- agent swarm;
- plugin marketplace abstraction;
- repository pattern around every storage class;
- CQRS/event sourcing;
- general policy DSL;
- generic workflow engine;
- extensive dependency injection framework.

One narrow backend protocol for Basic Memory and one host-adapter contract are enough.

## 7. Shared behavioral skill responsibilities

`skill/SKILL.md` should instruct the host model to:

1. search relevant approved knowledge when task context makes it useful;
2. identify possible additions/changed conditions/contradictions without claiming certainty about the user's internal knowledge;
3. propose at the earliest safe conversational checkpoint;
4. show the exact proposed content and relevant source scope;
5. offer Save/Edit/Skip;
6. never assume that tool permission equals knowledge approval;
7. optionally ask one appropriate learning/reflection question after saving;
8. treat any derived principle/explanation as a new proposal;
9. use retrieved knowledge with provenance/conditions/conflicts;
10. respect pause/target/fatigue/disable state;
11. avoid forcing practice when direct assistance is requested or safety/task completion requires an answer;
12. distinguish assistant-generated content from the user's own contribution.

The skill guides behavior. The service enforces persistence rules.

## 8. Coding standard for this MVP

Prefer small functions and direct code paths.

Every important domain invariant should be testable without launching a real host.

Host adapters should translate host events into the shared contract rather than duplicate domain logic.

When uncertainty exists, add a focused test and a short comment linking the behavior to the requirement. Do not solve uncertainty by adding abstraction layers.
