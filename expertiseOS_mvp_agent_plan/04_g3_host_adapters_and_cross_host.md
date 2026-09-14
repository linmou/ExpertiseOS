# 04 — G3 Host Adapters and Cross-Host Reliability

## Goal

Connect the already-tested core to Codex and Claude Code without duplicating domain rules.

The adapters are thin translation layers. They must provide:

- automatic activation after onboarding;
- normalized session/user/tool/checkpoint events;
- validated user-decision capture;
- safe learning checkpoints;
- shared local repository/state;
- graceful failure;
- capability reporting when a host/version cannot support a feature.

Do not move approval logic into prompts or host-specific code.

---

## 1. Shared adapter contract

Use the contract fixed in G0.

Each adapter must expose or internally produce these normalized facts:

```text
adapter_id
session_id
session_started
actual_user_event(event_ref, text_or_structured_action)
atomic_operation_started
atomic_operation_finished
safe_checkpoint_reached
session_ended
capabilities
```

Keep raw host payload parsing inside `hosts/codex.py` and `hosts/claude_code.py`.

The rest of expertiseOS should not import host SDK-specific event types.

---

## 2. Onboarding and activation

Implement a guided setup command/flow that:

1. detects supported host installations;
2. checks required versions/capabilities;
3. explains observation/storage/host-model boundaries;
4. obtains onboarding consent;
5. registers expertiseOS using supported host extension/plugin/hook mechanisms;
6. preserves unrelated existing host configuration;
7. starts/registers the shared local service;
8. runs a health check;
9. records enabled host capabilities;
10. makes uninstall reversible.

Do not require users to manually configure Python, databases, embedding providers, or a second model key.

If one host is unsupported, report it explicitly. Do not silently claim parity.

---

## 3. Safe checkpoint behavior

The adapter must prevent expertiseOS-initiated learning prompts while an atomic host operation is incomplete.

Minimal per-session state:

```text
atomic_depth or in_atomic_operation
comparison_due
active_proposal_id?
last_user_event_ref?
```

Rules:

- low-level events may set `comparison_due=true`;
- user-created scope exclusions are checked before expertiseOS observes/forwards source content for learning behavior;
- do not run fresh semantic candidate analysis after every low-level event;
- after the bounded operation completes, the next eligible conversational boundary may trigger search/comparison/proposal;
- an active storage decision should be presented before moving substantially beyond that insight when practical;
- ordinary task steps remain authorized even while a proposal is unresolved;
- if the next user message is unrelated to the active proposal, expire it by default.

Do not build a separate scheduler.

---

## 4. Validated Save/Edit/Skip capture

This is the critical host responsibility.

### Active proposal context

When the host displays a proposal, expertiseOS records only volatile binding information:

```text
proposal_id
session_id
adapter_id
content_digest
allowed actions
```

### User input processing

When a real user event arrives, adapter code checks whether it is an unambiguous response to the single active proposal.

Minimum rules:

- exact/clear Save -> register Save grant;
- clear Skip/cancel -> decline/expire proposal;
- Edit with explicit final content -> update/re-display proposal and bind the revised digest;
- Edit request without final content -> let the host model revise, re-display, then wait for Save;
- unrelated message -> expire unresolved proposal;
- multiple active proposals -> require disambiguation or itemized explicit actions;
- a direct user command to save clearly identified material may create and authorize the proposal from the same user event only under the narrow deterministic rules in `02_g1_core_consent_and_storage.md`;
- quoted Save text inside another message -> not a decision unless host interaction semantics clearly identify it as the response;
- model/tool output never creates a grant.

Do not make a natural-language classifier into a new standalone model service. Use deterministic parsing for clear controls and host-model clarification when ambiguous, without granting authorization until a later clear user event.

---

## 5. Session-end behavior

On host session end:

- expire unresolved candidates;
- delete unconsumed decision grants;
- clear declined fingerprints;
- do not persist recovery data containing candidate text;
- keep approved knowledge/evidence/control state intact.

A later host session must not be able to approve an old unresolved candidate.

---

## 6. Codex adapter

Implement `src/expertiseos/hosts/codex.py` using only G0-verified supported integration points.

Required verification:

- activation in a fresh supported session;
- current control state loaded without dumping full repository context;
- service/search tools available;
- atomic tool sequence not interrupted;
- user Save event creates matching decision grant;
- model-only attempted write is rejected;
- service outage does not block normal Codex work;
- session end clears volatile proposal state.

Document exact version/OS/permission mode in `docs/compatibility.md`.

---

## 7. Claude Code adapter

Implement `src/expertiseos/hosts/claude_code.py` against the same host-neutral contract.

Do not copy the Codex file and fork domain behavior.

Required verification mirrors Codex:

- activation;
- checkpoint safety;
- user-decision capture;
- failure-open task behavior;
- candidate expiry;
- accurate capability reporting.

If Claude's supported event model differs, normalize it inside the adapter and add host-specific contract tests.

---

## 8. Shared behavioral skill

Both hosts should load the same core behavioral specification.

Host packaging may require thin wrappers, but do not maintain two divergent product prompts.

The shared skill is responsible for model behavior such as:

- when to search;
- how to describe novelty uncertainty;
- when/how to propose;
- one-step optional reflection;
- recall usage;
- respecting control state.

The service remains responsible for writes/state integrity.

---

## 9. Cross-host shared state

Both adapters point to the same local expertiseOS service/repository.

Required behavior:

- stable object IDs across hosts;
- same approved content/provenance/relations;
- same learner state and controls;
- same reflection-period counts;
- pending proposals remain host-session scoped;
- approval never crosses sessions/hosts;
- concurrent stale edits fail via expected-version checks;
- a reflection/evidence event is not double-counted because both hosts later retrieve it.

Do not add synchronization infrastructure; both hosts are local clients of the same service.

---

## 10. Cross-host conflict fixture

Automate this scenario with fake adapters first, then reproduce against live hosts:

1. Codex reads knowledge object version 3 and proposes edit A.
2. Claude reads version 3 and proposes edit B.
3. user approves Claude edit B -> object becomes version 4.
4. user later approves Codex edit A.
5. service rejects Codex commit as stale.
6. Codex surfaces current version and requires re-proposal; it does not overwrite version 4.

---

## 11. Adapter capability reporting

At session start, expose only capabilities proven for the current host/version.

Suggested flags:

```text
can_read
can_search
can_validate_user_decisions
can_write
can_observe_atomic_boundaries
can_auto_activate
```

If approval validation is unavailable, `can_write=false`.

Do not hide degraded behavior behind optimistic prompts.

---

## 12. G3 tests

Unit/contract tests:

```text
test_host_contract.py
test_user_event_binding.py
test_safe_checkpoint.py
test_session_expiry.py
test_capability_reporting.py
```

Cross-host tests:

```text
test_shared_state.py
test_cross_host_no_approval_reuse.py
test_cross_host_version_conflict.py
test_cross_host_reflection_count.py
```

Live-host acceptance fixtures must cover at least:

- save;
- edit then save;
- skip;
- unrelated next message expiry;
- forged/model-only approval;
- atomic operation checkpoint;
- backend/service outage;
- switching hosts and retrieving the same object.

## G3 completion rule

Both hosts must satisfy the same domain contract. Host-specific exceptions belong in capability reporting and compatibility docs, not in weakened core semantics.
