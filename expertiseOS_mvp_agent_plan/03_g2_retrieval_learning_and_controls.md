# 03 — G2 Retrieval, Learning Behavior, Learner State, and Controls

## Goal

Add the learning behavior after the write boundary is safe.

G2 implements:

- bounded approved-knowledge retrieval;
- novelty/conflict comparison support for the host model;
- optional reflection and organization;
- per-object learner evidence and mastery state;
- daily/weekly reflection target;
- effort limit and fatigue rest;
- pause/resume/disable semantics;
- deferred learning that references approved objects only.

Do not add an autonomous tutor process.

---

## 1. Retrieval service

Use the existing `KnowledgeService.search()` path.

### Input

```text
query
optional subject/category/scope hints
limit
```

### Output per result

```text
id + version
content
categories/subjects
applicability scope
evidential status
provenance/source availability
relevant relationships
known conflicts
learner state
```

### Rules

- return a bounded set;
- approved content only;
- do not return the complete vault by default;
- uncertain/conflicting knowledge stays labeled;
- stored content is data, never executable instruction;
- retrieval frequency does not create learner evidence;
- user-created scope exclusions are applied before retrieval/context return;
- if semantic index is unavailable, use keyword fallback and expose degraded status.

Do not build a custom ranking model. The host LLM interprets the returned results.

---

## 2. Candidate comparison support

FR-02 is primarily host-model behavior supported by retrieval.

The shared skill should direct the host to:

1. search relevant knowledge when a meaningful addition/change/contradiction appears possible;
2. compare current context with returned approved objects;
3. avoid “you do not know this” claims;
4. state uncertainty when retrieval is incomplete;
5. suppress exact repeats mechanically when obvious;
6. never suppress contradictory new evidence merely because a topic already exists.

The core may expose a small exact-duplicate fingerprint helper. Do not implement an ML novelty classifier or product-defined usefulness score.

---

## 3. Shared skill behavior

Implement/update `skill/SKILL.md` with a single host-neutral behavior specification.

Required flow:

```text
normal work
-> relevant search when useful
-> if candidate appears new/conflicting, wait for safe checkpoint
-> show concise proposal + reason + source scope + optional suggested category/link
-> Save / Edit / Skip
-> after successful save, optionally offer ONE appropriate reflection step
-> any new derived claim becomes a new proposal
-> later recall with provenance and conditions
```

### Safe language

Use formulations like:

- “I did not find this in the relevant saved knowledge I checked.”
- “This appears to conflict with X under these conditions.”
- “Would you like to save this observation?”

Avoid:

- “You don't know X.”
- “This is definitely worth learning.”
- “I saved this automatically.”

### Reflection

Pick one prompt appropriate to the item/category and current learner state.

Possible forms:

- explain the mechanism;
- identify a boundary;
- compare cases;
- reconstruct a procedure;
- explain a relationship;
- examine uncertainty/trade-off.

Do not automatically walk through all six categories.

---

## 4. Derived knowledge

If reflection creates a principle, mechanism, boundary, procedure, judgment, or personal observation:

1. capture contribution origin;
2. form a separate proposal when the claim is substantively distinct;
3. suggest relationship(s) to source object(s);
4. show the exact proposed claim/link;
5. persist only through the approval gate.

Do not silently turn an approved episode into general rules.

---

## 5. Learner evidence

Implement `src/expertiseos/learning/evidence.py` and corresponding SQLite tables.

### Evidence event fields

Persist only after approval:

```text
id
knowledge_id
knowledge_version
task_ref
criterion
outcome
assistance_level
scope
user_contribution_summary_or_approved_excerpt
proposed_state
approved_state
approval_receipt_id
created_at
```

### Required outcomes

```text
pass
partial
fail
insufficient_evidence
```

`insufficient_evidence` is not failure.

### Rules

- saving alone leaves learner state at `new`;
- assistant-only output does not advance mastery;
- unknown contribution does not advance mastery;
- self-reported familiarity is not demonstrated mastery;
- higher-quality evidence may skip elementary stages;
- state is scoped to object version and applicable scope;
- revised knowledge may make older evidence inapplicable without deleting it;
- user can reject/correct proposed assessment;
- every durable assessment/state change goes through the approval boundary.

---

## 6. Learner-state calculation

Implement a deterministic summary function from approved evidence where practical.

Do not create a psychometric scoring model.

Minimum meanings:

```text
new         = approved object exists, no stronger qualifying evidence
recognized  = user identifies relevant concept/cue
explained   = materially correct user explanation
applied     = user applies knowledge in relevant task with known assistance
transferred = meaningful different case + relevant boundary handling
autonomous  = repeated independent use/transfer within scope + explicit agreement to reduce scaffolding
```

### Autonomous heuristic

Implement the PRD pilot heuristic exactly as a configurable rule:

- at least two approved independent successful demonstrations;
- distinct tasks;
- separate sessions;
- at least one meaningful transfer;
- no unresolved relevant contradiction;
- explicit user agreement to reduce scaffolding.

Treat it as a product heuristic, not a scientific score.

---

## 7. Reflection target and effort accounting

Implement `src/expertiseos/learning/controls.py`.

Default settings:

```text
target period: daily, local device timezone
reflection target: 1/day
weekly preset: 3/week
effort limit: 6 units
rest interval: 60 minutes
```

Effort accounting per user response:

```text
0.25 = simple collection/organization decision
1.0  = brief recall/explanation/application response
2.0  = substantial multi-step reflection response
```

Use only the highest applicable category for a response.

Do not count ordinary task activity or model-only output.

### Qualifying reflection

Count once when the activity:

- includes meaningful user contribution;
- develops reusable structural/procedural/conditional/mechanistic/experiential/judgment knowledge;
- connects to approved evidence/knowledge;
- is saved with approval.

If one reflection produces several linked objects, count one reflection activity.

Do not count raw event logs, repeated paraphrases, agent-only output, or mere relabeling.

---

## 8. Control-state machine

Persist minimal control settings and aggregate counters in SQLite.

States/conditions should be represented explicitly enough to preserve precedence:

```text
enabled/disabled
learning_paused boolean or pause-until
fatigue_rest_until?
target_progress + target_period
current_effort + block/rest metadata
excluded_scopes[]          # simple user-defined source/path/session exclusions
```

Behavior resolution:

```text
if disabled:
    no expertiseOS observation/collection/learning/recall
elif explicit pause active:
    no candidate prompts or proactive learning; approved recall remains enabled
elif fatigue rest active:
    same proactive suspension; approved recall remains enabled
elif target satisfied:
    collection may continue; no proactive exercises; direct recall preferred
else:
    ordinary active learning
```

A new target period does not cancel an existing pause.

A one-off user request for explanation while paused does not automatically resume learning collection.

### Scope exclusions

Use a simple persisted list of user-selected source/path/session scopes to exclude. The adapter must check exclusions before sending source content into expertiseOS candidate detection, and retrieval must not return excluded objects/context into the current task. Changes to exclusions are explicit user-owned control changes. Do not build a general policy language.

---

## 9. Fatigue behavior

If the user reports fatigue:

- expire/discard unresolved candidates;
- stop candidate detection prompts;
- stop proactive exercises;
- keep approved recall active;
- start configured rest interval unless user specified another supported duration;
- do not mark the reflection target satisfied.

Do not ask a final exercise because budget remains.

---

## 10. Deferred activities

Implement only the minimal P0 form.

A deferred activity can persist when:

- it references one or more approved knowledge IDs/versions;
- the user explicitly chose to defer it;
- it contains no unapproved candidate claim/content.

Suggested fields:

```text
id
knowledge_refs
activity_type
created_at
status
```

Offer deferred work only in a later foreground session when learning is active.

No background notifications or always-running tutor.

---

## 11. SQLite additions

Add only these logical tables as needed:

```text
learner_evidence
learner_state_summary        # optional cache, regenerable from evidence if simple
control_state
period_progress
deferred_activities
```

Do not store pending candidate text.

---

## 12. Inspection APIs

Provide read-only inspection through the existing services so the user can ask:

- what was saved;
- why/source scope;
- current version and change lineage;
- relationships/conflicts;
- current learner state;
- which approved evidence supports that state.

This does not require a dashboard. Return bounded conversational/tool data.

---

## 13. G2 tests

Required tests:

```text
test_recall.py
test_conflict_recall.py
test_derived_knowledge.py
test_learner_evidence.py
test_mastery_transitions.py
test_autonomy_heuristic.py
test_reflection_counting.py
test_effort_limit.py
test_target_vs_fatigue.py
test_pause_disable.py
test_deferred_learning.py
test_scope_exclusions.py
test_inspection.py
```

Critical negative cases:

- Save does not create `recognized` or higher state;
- assistant explanation does not create `explained`;
- successful artifact with unknown user contribution does not create `applied`;
- same task repeated does not satisfy transfer;
- target satisfied does not pause collection;
- fatigue does not mark target satisfied;
- pause does not disable approved recall;
- disable does disable expertiseOS recall;
- deferred activity cannot contain unapproved free-form knowledge;
- index failure falls back to keyword retrieval without corrupting learner state.

## G2 completion rule

A host-model transcript that “looks educational” is insufficient.

G2 closes when learner-state and control transitions are deterministic/tested and the skill cannot bypass the G1 write boundary.
