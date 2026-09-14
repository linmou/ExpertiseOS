# 01 — G0 Feasibility and Repository Bootstrap

## Goal

Resolve only the external uncertainties that can invalidate the design, then create the smallest repository skeleton needed for the remaining work.

Do not use G0 as an excuse to build product features.

## Exit criteria

G0 passes only when coding agents have evidence for all of the following:

1. Codex can activate the expertiseOS integration automatically after installation/onboarding.
2. Claude Code can activate the expertiseOS integration automatically after installation/onboarding.
3. For each host, there is a supported way to identify safe conversational checkpoints or conservatively approximate them.
4. For each host, there is a supported user-input path that the adapter can observe independently of model-supplied tool arguments.
5. The adapter can bind a user decision to an active expertiseOS proposal/session.
6. Normal host work still functions when expertiseOS service calls fail.
7. Basic Memory can be used locally behind an adapter without requiring a second generative-model API key.
8. Approved records can be retrieved and deleted through supported interfaces.
9. The chosen packaging approach has a documented Basic Memory AGPL-3.0 compliance decision/release constraint.
10. Exact tested host/dependency versions and operating-system scope are documented.

If an adapter cannot validate user approval, mark its write capability as blocked/read-only. Do not substitute model compliance for this missing boundary.

## Task 1 — Pin external versions

Create `docs/compatibility.md` with a table:

```text
component | tested version/commit | OS | capability | status | notes
Codex
Claude Code
Python
MCP SDK / host extension dependency
Basic Memory
local embedding dependency, if any
```

Use released/supported interfaces. Avoid private host internals.

## Task 2 — Verify the host adapter contract

Implement a temporary spike under `spikes/` or as throwaway tests, then remove unnecessary spike code before G0 closes.

For each host, answer these exact questions:

### Activation

- What supported install/registration mechanism activates expertiseOS in new sessions?
- Can the setup preserve existing host config?
- How does uninstall reverse the integration?

### Safe checkpoint

Identify the host events that can support these transitions:

```text
atomic operation begins
atomic operation ends
normal conversational handoff
session ends
```

The MVP does not need a perfect universal event stream. It needs a conservative rule that never injects a learning prompt while an atomic host tool operation is incomplete.

If the host lacks an explicit atomic-operation event, choose the narrowest safe supported boundary and document the limitation.

### Real user input

Prove that adapter code can observe an actual user-submitted message/event and can distinguish it from:

- assistant output;
- tool output;
- model arguments;
- quoted prior text.

The proof should include a small automated or reproducible manual fixture where:

1. a proposal is active;
2. the model tries to call a write tool without a user Save event;
3. the service rejects the write;
4. the user then submits Save through the host;
5. the adapter registers a matching decision grant;
6. the write succeeds exactly once.

### Session identity

Determine the stable session/conversation identifier available to the adapter.

If the host does not expose one, the adapter may generate an expertiseOS session ID at activation, but it must remain scoped to that host session and die with it.

## Task 3 — Verify Basic Memory capabilities

Through a narrow proof, verify:

- create approved knowledge;
- read by stable ID or deterministic mapping;
- search by keyword and/or local semantic index;
- attach metadata sufficient for category/subject/provenance/version/status;
- represent or reconstruct relationships;
- delete in-scope content/index entries;
- rebuild indexes;
- run locally after initial setup without a remote expertiseOS memory service.

Do not build against Basic Memory private database tables.

If stable versions/relationships are awkward, use the smallest sidecar mapping in SQLite needed to satisfy the requirement. Do not replace Basic Memory or fork it during G0.

## Task 4 — License/release note

Create `docs/basic-memory-license.md` containing:

- exact dependency/version reviewed;
- how it is distributed/started by expertiseOS;
- which AGPL obligations must be satisfied before public release;
- whether the current packaging is allowed for the intended showcase/pilot distribution;
- any release blocker.

Do not assume a process boundary eliminates AGPL obligations.

## Task 5 — Bootstrap the repository

Create only this initial structure:

```text
pyproject.toml
README.md
docs/
skill/
src/expertiseos/
tests/unit/
tests/integration/
tests/e2e/
```

Configure:

- package import;
- test command;
- lint/format only if the repository already uses one or a single lightweight choice is made;
- local development entrypoint for the service;
- no production web server unless the host integration requires one.

Prefer a local IPC/loopback transport supported by the selected MCP/host mechanism. Do not open an unauthenticated public listener.

## Task 6 — Define two narrow protocols

### `KnowledgeBackend`

Freeze only the methods needed by P0 behavior, approximately:

```python
create_approved(...)
get(id, version=None)
search(query, limit, scope=None)
update_approved(id, expected_version, ...)
set_relationships(...)
retire(id, expected_version)
delete(id)
rebuild_index()
health()
```

Do not add methods for hypothetical future team/cloud features.

### `HostAdapter`

Freeze only the shared concepts:

```text
adapter_id
session_id
capabilities
on_session_start
on_user_event
on_atomic_begin
on_atomic_end
on_checkpoint
on_session_end
register_decision_if_unambiguous
```

The exact method names can differ. The important outcome is that domain code receives normalized events rather than host-specific payloads.

## Task 7 — Create test doubles

Before feature development, provide:

- `FakeKnowledgeBackend` storing only approved test data in memory;
- `FakeHostAdapter` able to emit session/checkpoint/user events;
- deterministic clock/ID helpers if needed by tests.

These test doubles enable G1/G2 work without depending on live Codex/Claude sessions.

## G0 tests/checks

Add at minimum:

- backend contract smoke test;
- adapter contract smoke test;
- no-write-without-host-user-event proof;
- service unavailable does not block a host fixture;
- local backend works with network disabled after setup, where technically possible.

## Files expected from G0

```text
pyproject.toml
README.md
docs/compatibility.md
docs/basic-memory-license.md
docs/implementation-status.md
src/expertiseos/hosts/contract.py
src/expertiseos/knowledge/backend.py
tests/fakes.py
```

Do not implement learner state, export formats, dashboards, or a full Basic Memory mapping in this gate unless required to prove feasibility.
