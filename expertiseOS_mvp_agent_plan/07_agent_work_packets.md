# 07 — Agent Work Packets

## How to use this file

Each work packet is suitable for one coding agent. Agents should own distinct paths where possible and integrate through the contracts established in G0/G1.

Do not run all packets concurrently from the start. The core contracts must stabilize first.

## Dependency graph

```text
WP0
 |
 v
WP1
 |
 v
WP2
 |
 +-----------> WP3
 |              |
 |              +---------> WP4
 |              +---------> WP5
 |              +---------> WP6
 |              +---------> WP7
 |                           |
 +---------------------------+
              |
              v
             WP8
              |
              v
             WP9
```

Meaning:

- WP0 must finish first.
- WP1 and WP2 establish domain/approval invariants.
- WP3 stabilizes real backend/retrieval.
- WP4-WP7 may proceed in parallel after core interfaces are stable.
- WP8 integrates/adversarially validates.
- WP9 performs release documentation/final acceptance.

---

# WP0 — Feasibility and bootstrap

## Read first

- `final_plan.md`
- `00_scope_and_guardrails.md`
- `01_g0_feasibility_and_repo_bootstrap.md`

## Own

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

## Tasks

1. Verify/pin supported Codex and Claude Code integration paths.
2. Verify real user-input event availability and safe checkpoints.
3. Verify Basic Memory local create/read/search/delete and metadata/relations.
4. Decide exact minimal dependencies.
5. Create package/test skeleton and fakes.
6. Document blockers rather than weakening requirements.

## Stop condition

Do not hand off until the write-authorization path is feasible for each claimed write-capable host.

---

# WP1 — Domain model and volatile lifecycle

## Depends on

WP0.

## Own

```text
src/expertiseos/domain/models.py
src/expertiseos/domain/candidate_store.py
src/expertiseos/domain/errors.py
tests/unit/test_candidate_lifecycle.py
tests/unit/test_domain_models.py
```

## Tasks

1. Implement the minimal enums/models in `00_scope_and_guardrails.md`.
2. Implement candidate state machine.
3. Ensure candidate payloads have no durable serialization path.
4. Expire candidates on session end/unrelated next user message.
5. Add in-session decline suppression only in memory.
6. Cover illegal transitions.

## Interface handed to WP2

Stable `CandidateStore` methods + proposal ID/session/state/payload digest access.

---

# WP2 — Approval gate and exact writes

## Depends on

WP1.

## Own

```text
src/expertiseos/approval/
src/expertiseos/knowledge/service.py
src/expertiseos/state/sqlite.py
tests/unit/test_approval_gate.py
tests/unit/test_exact_write.py
tests/unit/test_decline_no_persistence.py
tests/unit/test_stale_approval.py
tests/unit/test_cross_session_approval.py
tests/unit/test_version_conflict.py
```

## Tasks

1. Implement one-use in-memory decision grants.
2. Implement canonical approval digest.
3. Enforce same proposal/session/adapter/action/content/version.
4. Implement commit ordering and approval receipts.
5. Add idempotency/reconciliation for partial write/receipt failure.
6. Implement create/revise/relation/retire proposal paths against fake backend.
7. Prove forged/model-only/cross-session approvals fail.

## Important

Do not accept a boolean approval parameter as authorization.

## Interface handed to later packets

Stable guarded `KnowledgeService` mutation API and approval receipt semantics.

---

# WP3 — Basic Memory adapter and retrieval

## Depends on

WP2 plus G0 backend proof.

## Own

```text
src/expertiseos/backends/basic_memory.py
src/expertiseos/knowledge/backend.py   # only narrow compatible changes
retrieval-related portions of src/expertiseos/knowledge/service.py
tests/integration/test_basic_memory_adapter.py
tests/integration/test_recall.py
tests/integration/test_provenance.py
tests/integration/test_relationships.py
```

## Tasks

1. Map expertiseOS IDs/versions/metadata to Basic Memory.
2. Map provenance and relations.
3. Implement bounded search and keyword fallback.
4. Return conflicts/relationships with reads.
5. Ensure decline path creates no backend/index record.
6. Verify delete/index rebuild.
7. Keep Basic Memory internals out of domain modules.

## Stop condition

Canonical approved knowledge must round-trip exactly before host adapters rely on it.

---

# WP4 — Learner evidence and learning controls

## Depends on

WP2; WP3 retrieval interface must be known before final integration.

## Own

```text
src/expertiseos/learning/evidence.py
src/expertiseos/learning/controls.py
learning/control migrations in src/expertiseos/state/sqlite.py
tests/unit/test_learner_evidence.py
tests/unit/test_mastery_transitions.py
tests/unit/test_autonomy_heuristic.py
tests/unit/test_reflection_counting.py
tests/unit/test_effort_limit.py
tests/unit/test_target_vs_fatigue.py
tests/unit/test_pause_disable.py
tests/unit/test_deferred_learning.py
```

## Tasks

1. Implement approved learner-evidence records.
2. Implement per-object/version/scope mastery summary.
3. Keep self-report distinct from demonstrated mastery.
4. Implement exact autonomous heuristic.
5. Implement reflection target/effort/rest defaults.
6. Implement pause/fatigue/target/disable precedence.
7. Implement minimal deferred activities referencing approved objects only.

## Important

All durable learning-evidence/state changes pass through WP2 approval semantics.

---

# WP5 — Codex adapter and onboarding path

## Depends on

WP2 and stable HostAdapter contract; may use fake backend until WP3 merges.

## Own

```text
src/expertiseos/hosts/codex.py
Codex-specific install/onboarding glue
Codex contract/e2e tests
docs/compatibility.md Codex rows
```

## Tasks

1. Implement supported activation path.
2. Normalize session/user/atomic/checkpoint events.
3. Register decision grants only from actual Codex user events.
4. Expire proposal on unrelated next user event/session end.
5. Verify service failure does not block normal work.
6. Report capabilities accurately.

## Do not

- duplicate approval logic;
- parse tool/model output as user authorization;
- add Codex-only domain behavior.

---

# WP6 — Claude Code adapter and onboarding path

## Depends on

Same dependencies as WP5.

## Own

```text
src/expertiseos/hosts/claude_code.py
Claude-specific install/onboarding glue
Claude contract/e2e tests
docs/compatibility.md Claude rows
```

## Tasks

Mirror WP5 using Claude Code's verified supported integration points.

Normalize differences inside the adapter.

Do not change shared domain semantics to accommodate host quirks. Use capability reporting if a feature cannot be supported safely.

---

# WP7 — Export/delete/reliability/security

## Depends on

WP2; integrates with WP3 backend when available.

## Own

```text
export/restore module(s) under src/expertiseos/
delete/uninstall support
reliability helpers needed by service/backend
security boundary tests
benchmark script/test
tests/integration/test_export_restore.py
tests/integration/test_retire_delete.py
tests/integration/test_backend_outage.py
tests/integration/test_index_failure_rebuild.py
tests/integration/test_idempotent_retry.py
tests/integration/test_injection_boundary.py
tests/integration/test_no_candidate_persistence_audit.py
```

## Tasks

1. Portable export/restore.
2. Retire/delete semantics.
3. Uninstall keep/delete choice.
4. Backend/index degradation.
5. Startup recovery from approved state only.
6. Injection-resistant service boundary.
7. Persistent-store negative audit.
8. Performance measurement harness.

---

# WP8 — Integration, shared skill, and full acceptance

## Depends on

WP3-WP7 merged.

## Own

```text
skill/SKILL.md
src/expertiseos/service.py
src/expertiseos/mcp_server.py
tests/e2e/
examples/reference_scenarios/
```

## Tasks

1. Wire tool surface to guarded services.
2. Ensure host-facing write tools cannot bypass approval gate.
3. Implement shared behavioral skill.
4. Implement/reference Scenario A-D fixtures.
5. Run AT-01 through AT-16.
6. Add cross-host stale edit and no-cross-approval tests.
7. Run adversarial note/tool fixtures.
8. Run no-network/local fallback fixture.

## Integration rule

If an E2E failure exposes missing domain behavior, fix it in the owning core module. Do not patch the host prompt to hide a persistence/state bug.

---

# WP9 — Release docs and final verdict

## Depends on

WP8.

## Own

```text
README.md
docs/architecture.md
docs/privacy-boundary.md
docs/compatibility.md
docs/implementation-status.md
```

## Tasks

1. Document actual architecture, not planned architecture.
2. List exact tested host/dependency versions.
3. Explain local-first boundary and host-provider processing.
4. Explain approval boundary and what is/not protected.
5. Document degraded modes and unsupported surfaces.
6. Fill acceptance matrix with evidence.
7. Document performance measurements.
8. Document install/uninstall/export/delete commands.

## Final verdict categories

Use one of:

```text
PASS
PASS WITH DOCUMENTED COMPATIBILITY LIMIT
BLOCKED — REQUIREMENT NOT SAFELY IMPLEMENTABLE
```

Do not call the MVP complete if a P0 consent/privacy/state-integrity test fails.

---

## Merge-conflict guidance

Avoid concurrent edits to these central files unless coordinated:

```text
src/expertiseos/knowledge/service.py
src/expertiseos/state/sqlite.py
src/expertiseos/service.py
src/expertiseos/mcp_server.py
skill/SKILL.md
```

Preferred ownership sequence:

- WP2 establishes `knowledge/service.py` and SQLite base.
- WP4 adds learner/control migrations through a small follow-up.
- WP3 changes only backend/retrieval-facing service methods.
- WP8 performs final wiring after all owners merge.

## Agent completion template

Each coding agent should finish its packet with a short note in `docs/implementation-status.md`:

```text
Work packet:
Implemented:
Tests added/run:
External assumptions verified:
Known limitation/blocker:
Files intentionally not added:
```

This prevents later agents from guessing about incomplete behavior.
