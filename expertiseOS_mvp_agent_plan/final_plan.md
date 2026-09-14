# expertiseOS MVP — Agentic Coding Implementation Plan

## Purpose

This directory is the implementation plan for coding agents building the full expertiseOS MVP described in `expertiseOS_MVP_PRD(4).md`.

The plan intentionally avoids speculative architecture. Build only what is required to satisfy the MVP requirements and acceptance tests.

## Source of truth

Implementation decisions must preserve these product invariants:

1. The host agent owns the user's work. expertiseOS does not become the task orchestrator.
2. Unapproved candidate content never becomes expertiseOS-controlled persistent data.
3. Every substantive knowledge write, semantic edit, relation change, conflict resolution, learner-evidence write, and mastery change is bound to a real user authorization.
4. The host LLM performs semantic interpretation. expertiseOS does not add a second generative model or require another API key.
5. Basic Memory stays behind a narrow backend adapter. Do not expose unrestricted backend writes to the host model.
6. Codex and Claude Code share one local repository and one behavioral contract.
7. Recall, mastery, provenance, and user permission are separate concepts.
8. Learning interactions never block unrelated authorized work.
9. Pause, fatigue rest, target-satisfied behavior, and full disable are distinct states.
10. The implementation must pass the deterministic acceptance suite, not merely produce a convincing demo transcript.

Read `00_scope_and_guardrails.md` before changing code.

## Minimal implementation shape

Use one local Python package and one local service process.

```text
Codex adapter ---------\
                       \
                        > expertiseOS local service/core ---> Basic Memory adapter ---> local Basic Memory store
                       /
Claude Code adapter ---/               |
                                       +--> local SQLite state.db
                                            approvals/evidence/controls/deferred work
```

Important constraints:

- Volatile candidates and unconsumed approval grants stay in memory only.
- Approved knowledge, provenance, relationships, and knowledge versions live through the backend adapter.
- Learner evidence, control state, approval receipts, and deferred-learning references live in a small local SQLite database.
- Search indexes contain approved knowledge only.
- Do not add Redis, a job queue, a graph database, a web dashboard, a background worker, an event-sourcing framework, CQRS, or a separate policy engine.

The exact Codex/Claude hook APIs and exact Basic Memory package/version are deliberately resolved in G0 before integration code is committed.

## Execution order

### Gate G0 — Feasibility and repository bootstrap

Use `01_g0_feasibility_and_repo_bootstrap.md`.

Deliverables:

- pinned tested host/dependency versions;
- verified user-input capture path for Codex and Claude Code;
- verified safe-checkpoint integration points;
- verified local-only backend/search path;
- Basic Memory license/packaging note;
- repository skeleton and CI test command;
- host adapter contract frozen enough for core implementation.

Do not weaken approval semantics if a host cannot satisfy the contract. That host remains read-only until a trustworthy path is found.

### Gate G1 — Consent, candidate lifecycle, canonical storage

Use `02_g1_core_consent_and_storage.md`.

Build first:

- domain models;
- volatile candidate lifecycle;
- host-originated decision grant;
- approval gate;
- exact approved writes;
- provenance;
- versions and optimistic concurrency;
- relationships;
- Basic Memory adapter;
- no-persistence-on-decline/crash tests.

This gate contains the highest-risk product invariant. Do not start learning features before the approval boundary is covered by tests.

### Gate G2 — Retrieval, learning behavior, mastery, learning controls

Use `03_g2_retrieval_learning_and_controls.md`.

Build:

- bounded retrieval with provenance/conflicts;
- candidate comparison support;
- six-category reflection behavior in the shared skill;
- learner evidence and per-object mastery;
- reflection target;
- effort accounting;
- fatigue/pause/disable behavior;
- deferred activities that only reference approved objects.

Do not implement a second tutor process or automatic background reflection.

### Gate G3 — Both hosts and cross-host reliability

Use `04_g3_host_adapters_and_cross_host.md`.

Build and verify:

- thin Codex adapter;
- thin Claude Code adapter;
- automatic activation after onboarding;
- actual user-event binding;
- safe checkpoints;
- session-scoped proposals;
- cross-host version conflicts;
- shared local state;
- fail-open-for-work behavior.

### Reliability/privacy completion

Use `05_export_delete_reliability_security.md`.

Build:

- export/restore;
- retire/delete;
- index rebuild and backend failure handling;
- idempotent retries;
- injection resistance at the service boundary;
- local transport/access control;
- degraded keyword-search mode;
- uninstall data choice.

These are P0 even though they are not the first features to implement.

### Final acceptance

Use `06_acceptance_and_e2e.md`.

The MVP is not complete until AT-01 through AT-16 pass for each required host where applicable, plus the cross-host suite.

## Files in this plan

| File | Purpose |
|---|---|
| `00_scope_and_guardrails.md` | Product invariants, implementation defaults, explicit non-goals, anti-overdesign rules. |
| `01_g0_feasibility_and_repo_bootstrap.md` | Host/backend feasibility spike and minimal project bootstrap. |
| `02_g1_core_consent_and_storage.md` | Candidate lifecycle, approval binding, canonical writes, provenance, versioning, relations. |
| `03_g2_retrieval_learning_and_controls.md` | Retrieval, reflection, mastery, target/effort/pause/deferred behavior. |
| `04_g3_host_adapters_and_cross_host.md` | Codex/Claude adapters, safe checkpoints, validated user events, shared state. |
| `05_export_delete_reliability_security.md` | Export/delete, retries, indexing, local security, failure semantics. |
| `06_acceptance_and_e2e.md` | Deterministic acceptance suite and end-to-end fixtures. |
| `07_agent_work_packets.md` | Concrete coding-agent assignments, dependencies, owned paths, and merge order. |
| `08_traceability_matrix.md` | Mapping from FR/NFR/AT requirements to implementation areas and tests. |

## Target repository layout

Keep the repository small. The initial target is:

```text
expertiseOS/
├── pyproject.toml
├── README.md
├── docs/
│   ├── architecture.md
│   ├── compatibility.md
│   ├── privacy-boundary.md
│   └── implementation-status.md
├── skill/
│   └── SKILL.md
├── src/expertiseos/
│   ├── __init__.py
│   ├── service.py
│   ├── mcp_server.py
│   ├── domain/
│   │   ├── models.py
│   │   ├── candidate_store.py
│   │   └── errors.py
│   ├── approval/
│   │   └── gate.py
│   ├── knowledge/
│   │   ├── service.py
│   │   └── backend.py
│   ├── learning/
│   │   ├── evidence.py
│   │   └── controls.py
│   ├── state/
│   │   └── sqlite.py
│   ├── backends/
│   │   └── basic_memory.py
│   └── hosts/
│       ├── contract.py
│       ├── codex.py
│       └── claude_code.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── examples/
    └── reference_scenarios/
```

Do not create additional layers until a requirement or a failing test demands them.

## Core service contracts to stabilize early

The exact MCP names may differ, but the domain behavior should converge on these operations:

### Read operations

- `search_knowledge(query, limit, scope?)`
- `get_knowledge(id, version?)`
- `inspect_learning_state(knowledge_id)`
- `inspect_controls()`

### Proposal operations

- `propose_create_knowledge(...)`
- `propose_revision(...)`
- `propose_relation_change(...)`
- `propose_learning_evidence(...)`
- `decline_proposal(proposal_id)`

### Commit path

A persistent mutation succeeds only when all are true:

1. the proposal is active and belongs to the same host session;
2. the adapter has registered a fresh user decision from the real host input path;
3. the decision matches the proposal/action and displayed content binding;
4. expected object versions still match;
5. the backend write succeeds durably;
6. only then is the approval receipt written and success returned.

The model cannot create this authorization by passing `approved=true`, quoting a user, or replaying an old event.

### Control/user-owned operations

- pause/resume learning;
- disable/enable expertiseOS;
- set reflection target/effort limit;
- export/restore;
- retire/delete knowledge;
- remove deferred activity.

Use the same exact-approval principle where the operation changes durable semantic/user state.

## Coding-agent rules

Every agent must:

1. Read this index, `00_scope_and_guardrails.md`, and its assigned work packet before editing.
2. Inspect the existing repository before creating new files. Reuse simple existing structure when compatible.
3. Implement the smallest requirement-complete path, not a framework for future features.
4. Add or update tests in the same change as production code.
5. Keep domain behavior host-neutral. Host-specific event parsing stays under `hosts/`.
6. Never bypass the approval gate to make an end-to-end test easier.
7. Never persist candidate text for logging/debugging.
8. Never infer mastery from saving, retrieval frequency, or model-only output.
9. Never add a new external service or remote API without a PRD requirement.
10. Record unresolved feasibility limits in `docs/implementation-status.md` rather than silently changing product behavior.

## Merge/integration order

Use the work-packet dependency graph in `07_agent_work_packets.md`.

At a high level:

```text
WP0 feasibility/bootstrap
  -> WP1 domain + volatile candidate lifecycle
  -> WP2 approval gate + exact writes
  -> WP3 Basic Memory + retrieval
       -> WP4 learner evidence + controls
       -> WP5 Codex adapter
       -> WP6 Claude adapter
       -> WP7 export/delete/reliability
  -> WP8 cross-host + adversarial acceptance
  -> WP9 release docs + final acceptance report
```

WP4, WP5, WP6, and much of WP7 can proceed in parallel only after the core interfaces and test doubles are stable.

## Definition of done for the coding effort

Do not declare completion because all modules exist.

Completion requires:

- both required host integrations are tested on pinned versions;
- no unapproved expertiseOS content persists in the negative-path fixtures;
- exact content/version approval binding is demonstrated;
- shared repository and cross-host conflict handling work;
- learner evidence remains distinct from knowledge validity and permission;
- target/fatigue/pause/disable transitions are correct;
- export/restore/delete are verified;
- backend/index failures do not block ordinary host work or falsely report success;
- AT-01 through AT-16 have reproducible results documented in `docs/implementation-status.md`.
