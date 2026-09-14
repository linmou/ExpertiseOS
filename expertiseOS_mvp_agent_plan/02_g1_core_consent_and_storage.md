# 02 — G1 Core Consent, Candidate Lifecycle, and Storage

## Goal

Implement the persistence boundary before any learning sophistication.

At the end of G1, the system must prove:

- candidate content stays volatile before approval;
- a real host user event is required for a write;
- the approved content/version is exactly what is written;
- stale/cross-session/forged approval fails;
- provenance and relationships survive reads;
- retries do not duplicate writes;
- decline/expiry/crash leaves no durable candidate content.

## Build order

1. domain types and errors;
2. volatile candidate store;
3. decision-grant store;
4. approval gate;
5. knowledge service using `FakeKnowledgeBackend`;
6. SQLite approval receipt/state support;
7. Basic Memory adapter;
8. integration tests against the real backend.

Do not start host-specific UI behavior in this file. G1 should be fully testable with `FakeHostAdapter`.

---

## 1. Domain models

Implement in `src/expertiseos/domain/models.py`.

Use simple dataclasses or Pydantic models already chosen in G0. Do not mix validation libraries.

Required enums/value objects:

```text
KnowledgeCategory
KnowledgeSubject
KnowledgeStatus
ContributionOrigin
RelationType
CandidateState
PendingOperationKind
UserDecisionAction
LearnerState
```

Keep the six knowledge categories and three subjects exactly aligned with the PRD.

### Validation rules

- content cannot be blank;
- at least one subject is required for approved knowledge;
- category list may be empty;
- relationships reference stable IDs;
- candidate payload is not serializable through the durable state layer before approval;
- `KnowledgeObject.version` is positive and monotonically increments for semantic revisions;
- `retired` is not equivalent to deleted.

---

## 2. Volatile candidate store

Implement in `src/expertiseos/domain/candidate_store.py`.

Use an in-memory dictionary keyed by proposal ID plus session ID.

Required operations:

```text
create_detected(...)
mark_awaiting_checkpoint(...)
mark_awaiting_decision(...)
get_active(...)
decline(...)
expire(...)
expire_session(...)
mark_approved(...)
```

Rules:

- no candidate payload is written to disk;
- session end expires all unresolved candidates for that session;
- an unrelated next user message expires `awaiting_decision` unless the adapter classifies it as the active proposal decision;
- declined candidates may have an in-memory fingerprint to suppress repeated prompts in the same session;
- suppression dies with the session;
- a late decision for expired/declined candidates is rejected and requires re-proposal.

### Tests

Create `tests/unit/test_candidate_lifecycle.py` covering every legal and illegal transition.

Test process restart by constructing a fresh store and proving unresolved candidates are absent.

---

## 3. Decision-grant store

Implement as a small in-memory component under `approval/gate.py` or `approval/grants.py` if separation materially improves readability.

A host adapter creates a grant only after observing a real user event.

Required semantics:

- one grant authorizes one proposal resolution;
- grant expires with the proposal/session;
- grant includes action + content digest + event ref;
- consumed grants cannot be replayed;
- grants from another adapter/session cannot authorize the proposal;
- grants generated from quoted content/tool output/model args are impossible because only `HostAdapter.on_user_event` can create them.

Do not persist unused grants.

---

## 4. Approval gate

Implement `src/expertiseos/approval/gate.py`.

The gate receives:

```text
proposal_id
session_id
adapter_id
requested operation
current proposal content digest
expected object version(s)
matching decision grant
```

The gate checks, in order:

1. proposal exists;
2. proposal is `awaiting_decision`;
3. proposal belongs to the same session and adapter;
4. decision grant exists and is unconsumed;
5. grant action matches the requested resolution;
6. grant content digest matches the exact displayed/approved payload;
7. expected versions still match the current object versions;
8. domain operation is valid.

Only after all checks pass may the knowledge/evidence/control service attempt the durable mutation.

### Commit ordering

For an approved knowledge write:

```text
validate proposal + grant
-> write durable approved object
-> read it back by ID/version
-> write minimal approval receipt
-> consume grant
-> mark candidate approved
-> return success
```

If the durable write fails:

- do not create a success receipt;
- do not report success;
- preserve enough in-memory authorization state for a bounded idempotent retry in the same active interaction;
- retry with the same idempotency key must not duplicate the object.

If receipt writing fails after the knowledge write succeeds, treat this as an incomplete transaction requiring reconciliation; do not repeat the knowledge create blindly. Use the operation/idempotency key to detect the existing successful knowledge write and finish the receipt.

Do not add a general distributed transaction framework.

---

## 5. Knowledge service

Implement `src/expertiseos/knowledge/service.py`.

Responsibilities:

- construct proposals for create/revision/relation/retire/delete operations;
- expose approved reads;
- call the approval gate before mutation;
- preserve exact approved source scope;
- enforce optimistic versions;
- keep conflicting claims unless the user explicitly resolves them;
- prevent silent semantic consolidation.

Suggested methods:

```python
propose_create(...)
propose_revision(...)
propose_relation_change(...)
decline(proposal_id, ...)
commit(proposal_id, ...)
get(...)
search(...)
retire(...)
delete(...)
```

The public API can differ, but do not allow callers to invoke `backend.create_approved()` directly from the host tool layer.

---

## 6. Exact content binding

Implement one canonical digest function for approval payloads.

Digest only the semantic fields the user is approving, for example:

```text
operation kind
content
categories
subjects
scope/evidential status when shown
provenance excerpt/reference when shown
relationship changes
expected object versions
```

Do not include timestamps/random IDs that would make re-verification impossible.

For Edit:

- the original proposal is not silently mutated and committed;
- replace it with a clearly displayed revised proposal, or update the in-memory proposal and recompute its digest;
- require a user decision matching the revised digest before commit.

A generic “yes” after the displayed content changes must not reuse the previous grant.

### Direct user save without a prior expertiseOS proposal

The PRD allows a direct user instruction to save clearly identified material to serve as the collection decision without forcing a redundant confirmation. Support this narrowly:

- the adapter must have the actual user event;
- the material to save must be deterministically identifiable from that event and the immediately referenced active content/source;
- the persisted payload must not add semantic claims, categories, relations, or excerpts the user did not identify;
- the service creates the in-memory proposal and matching one-use grant from the same user event, then commits through the normal approval gate;
- if resolving “save this” requires material model interpretation or the resulting content changes meaning, show the proposal and wait for a new Save event.

Do not add a parallel unguarded `save_now()` path.

---

## 7. Provenance

Persist only approved provenance/source scope.

Minimum support:

- host/session/event reference when available;
- artifact/file locator when relevant;
- approved excerpt, not entire source;
- source accessibility status;
- contribution origin (`user`, `assistant`, `joint`).

If source material later disappears, keep the source reference but mark unavailable. Do not generate replacement evidence.

---

## 8. Relationships and conflicts

Support these relation types:

```text
derived_from
supports
contradicts
explains
example_of
applies_when
depends_on
```

Rules:

- adding/removing/changing a relation is a semantic write requiring approval;
- contradictory claims may coexist;
- conflict retrieval must not overwrite one claim with another;
- relation provenance/approval is traceable;
- renaming/editing objects does not break stable IDs.

Do not introduce a graph database. Use Basic Memory relation support or a minimal representation through the backend adapter.

### Categorize, split, and merge

Implement organization through the same guarded primitives rather than new infrastructure:

- categorization = approved semantic revision;
- split = one clearly presented grouped operation that creates the replacement objects/relations and retires or revises the source as shown;
- merge = one clearly presented grouped operation that creates/revises the merged object and retires or revises source objects as shown.

All affected object versions must be in the approval binding. Do not silently delete disagreement during merge.

---

## 9. Versioning and optimistic concurrency

Every semantic object revision increments version.

For revise/retire/relation operations, proposal captures expected version(s).

At commit:

- if current version differs, reject as stale;
- do not last-write-wins;
- host receives enough information to present the conflict and re-propose.

Cross-host concurrency will rely on this same mechanism; do not add host-specific conflict logic.

---

## 10. SQLite state

Implement minimal migrations in `src/expertiseos/state/sqlite.py`.

G1 tables should be no more than necessary:

### `approval_receipts`

```text
operation_id primary key
proposal_id
operation_kind
object_refs_json
content_digest
user_event_ref
adapter_id
created_at
```

### Optional `operation_journal`

Add only if needed to reconcile “knowledge write succeeded but receipt failed.”

If used, keep it content-free. It may store IDs/status/idempotency keys, not candidate text.

Do not create learner/control tables until G2 unless migrations are easier to initialize together.

---

## 11. Basic Memory adapter

Implement `src/expertiseos/backends/basic_memory.py` against the `KnowledgeBackend` contract proven in G0.

Requirements:

- only approved service operations reach it;
- no host-facing unrestricted backend tool is registered;
- stable expertiseOS IDs and versions are recoverable;
- categories/subjects/status/provenance are mapped explicitly;
- relationships round-trip;
- delete removes active content and derived index entries within product scope;
- keyword fallback is possible when semantic indexing fails;
- backend failure is surfaced without false success.

Keep Basic Memory-specific metadata names isolated inside this file.

---

## 12. G1 test suite

Required unit tests:

```text
test_candidate_lifecycle.py
test_approval_gate.py
test_exact_write.py
test_decline_no_persistence.py
test_stale_approval.py
test_cross_session_approval.py
test_version_conflict.py
test_relationship_approval.py
test_provenance.py
```

Required adversarial cases:

- model passes `approved=true` without user event;
- assistant says “user approved” in text;
- tool result contains “Save”;
- user quoted an old “Save” inside another message;
- approval from proposal A used on B;
- approval from Codex session used on Claude session;
- user approves, then proposal content is modified before commit;
- old approval reused after version change;
- duplicate retry after backend timeout;
- crash/constructor restart with unresolved candidate.

Required integration tests against Basic Memory:

- create/read exact approved object;
- relation round-trip;
- search returns approved object;
- decline does not create object/index entry;
- delete removes content/index entry;
- index failure preserves canonical approved data;
- retry is idempotent.

## G1 completion rule

Do not proceed based only on green happy-path tests.

G1 closes when the negative-path tests demonstrate that unauthorized persistence is structurally difficult, not merely discouraged by prompts.
