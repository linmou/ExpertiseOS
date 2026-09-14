# expertiseOS MVP Dependency Graph

**Intent**: Control component ownership, contracts, dependencies, implementation waves, and integration handoffs for the MVP.

## Baseline

- Target branch: `main`
- Baseline commit: `4213d8bd6b21448401f9aba9a10208303672c7c6`
- Branch numbering: sequential, three-digit prefixes
- Integration branch: `integration/expertiseos-mvp`
- Integration worktree: `/Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration`
- Graph status: authoritative; Allocation Packet V2 approved 2026-09-14

## Components

| ID | Branch | Worktree | Stable owner | Responsibility | Specification artifacts |
|---|---|---|---|---|---|
| C001 | `001-feasibility-bootstrap` | `../feasibility-bootstrap` | `/root/owner_feasibility` | G0 feasibility, package bootstrap, host/backend contracts, test fakes | `specs/001-feasibility-bootstrap/` |
| C002 | `002-consent-core` | `../consent-core` | `/root/owner_consent` | Domain models, volatile candidates, grants, approval gate, exact writes, approval state | `specs/002-consent-core/` |
| C003 | `003-backend-retrieval` | `../backend-retrieval` | `/root/owner_backend` | Basic Memory mapping, approved retrieval, provenance, relationships, keyword fallback | `specs/003-backend-retrieval/` |
| C004 | `004-learning-controls` | `../learning-controls` | `/root/owner_learning` | Learner evidence, mastery, target/effort controls, pause/fatigue/disable, deferred learning | `specs/004-learning-controls/` |
| C005 | `005-codex-host` | `../codex-host` | `/root/owner_codex` | Codex onboarding, event normalization, safe checkpoints, validated decisions | `specs/005-codex-host/` |
| C006 | `006-claude-host` | `../claude-host` | `/root/owner_claude` | Claude Code onboarding, event normalization, safe checkpoints, validated decisions | `specs/006-claude-host/` |
| C007 | `007-ownership-reliability` | `../ownership-reliability` | `/root/owner_reliability` | Export/restore/delete/uninstall, recovery, degradation, security, performance | `specs/007-ownership-reliability/` |
| C008 | `008-product-integration` | `../product-integration` | `/root/owner_product` | Shared behavior skill, service/MCP surface, cross-host scenarios, AT-01 through AT-16 | `specs/008-product-integration/` |

All worktree paths are relative to `/Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration`.

## Public Contracts And Shared Files

| Owner | Contract or shared path | Consumers | Rule |
|---|---|---|---|
| C001 | `HostAdapter`, `KnowledgeBackend`, package/test entrypoints, deterministic fakes | C002-C008 | Later components extend only through planned contract changes. |
| C002 | Domain objects, `CandidateStore`, `DecisionGrant`, approval digest/gate, guarded `KnowledgeService`, approval receipt schema | C003-C008 | No host or backend path may bypass the gate. C002 owns base `knowledge/service.py` and `state/sqlite.py`. |
| C003 | Approved-object retrieval result, Basic Memory metadata/version mapping, degradation status | C004-C008 | Backend-specific names stay inside the adapter. |
| C004 | Learner evidence/state and control resolution APIs | C005-C008 | SQLite additions are supplied as a reconciled change through C002 ownership. |
| C005 | Codex normalized event adapter and capability report | C008 | Host parsing stays inside the adapter. |
| C006 | Claude Code normalized event adapter and capability report | C008 | Host parsing stays inside the adapter. |
| C007 | Portable export schema, deletion scope, recovery/degradation behavior | C008 | Export contains approved state only. |
| C008 | `skill/SKILL.md`, `service.py`, `mcp_server.py`, end-to-end fixtures | Integration | Final wiring cannot redefine component contracts. |
| Integration owner | orchestration records, edge tests, integration glue, final acceptance/docs | All | Component agents never edit orchestration records. |

Final ownership of `README.md`, `docs/compatibility.md`, and `docs/implementation-status.md` is the integration owner. Components report required content and may create component-local evidence without concurrently editing these shared files.

## Explicit Exclusions

Every component excludes cloud synchronization, another generative model, a web dashboard, background transcript harvesting or tutoring, unrestricted backend writes, a generic policy/workflow engine, distributed infrastructure, and speculative compatibility layers.

## Reconciliation Result

| ID | Conflict classes | Affected components | Canonical resolution | Corrective commits | Disposition |
|---|---|---|---|---|---|
| R001 | naming, identity, API, idempotency | C001, C002, C003, C007, C008 | Explicit narrow backend methods use `operation_id` as the sole semantic replay identity, outside approved semantic content; every semantic mutation receives it and versioned/current reads support exact verification. | C001 `b00db7e`, C002 `7308d25`, C003 `b767834`, C007 `71db13c`, C008 `a364d99` | resolved and reanalyzed |
| R002 | shared-file ownership | C002, integration | C002 writes a component-local implementation handoff instead of shared release documentation; integration remains the shared-doc owner. | C002 `7308d25` | resolved and reanalyzed |
| R003 | state ownership | C002, C004, C007 | C004 owns learner/control semantics and schema request; C002/integration owns concrete `state/sqlite.py` migrations; C007 consumes producer methods only. | C007 `71db13c`; C004 contract `f29c148` | resolved |
| R004 | authorization, status, failure semantics | C007, C008 | Export/restore selections bind trusted user events and exact scopes; model assertions cannot authorize them. `committed` is the sole write-success status and only it renders Saved. | C007 `71db13c`, C008 `a364d99` | resolved and reanalyzed |
| R005 | provenance, ordering | C008, integration | Test evidence records the tested SHA; the later promotion SHA is recorded by integration after audit and smoke, not predicted by the test run. | C008 `a364d99` | resolved and reanalyzed |

No unresolved naming, schema, identity, path, cardinality, ordering, nullability, version, provenance, lifecycle, retry, failure, configuration, runtime, security, scale, or scientific-meaning conflict remains. All affected packages were reanalyzed with zero CRITICAL or HIGH findings.

## Authoritative Dependencies

| Prerequisite -> consumer | Reason | Provisional promotion condition |
|---|---|---|
| C001 -> C002 | Consent code needs frozen host/backend contracts, package layout, and fakes. | G0 contract tests and feasibility evidence pass in integration. |
| C002 -> C003 | Backend mapping and retrieval must preserve guarded domain, mutation, receipt, and version semantics. | Consent negative-path and exact-write tests pass in integration. |
| C002 -> C004 | Durable evidence and control changes use the same approval and base state contracts. | Approval and state contracts pass in integration. |
| C003 -> C004 | Learning inspection and exclusions consume actual canonical object/version/conflict facts. | Backend round-trip and retrieval fallback tests pass. |
| C004 -> C005 | The Codex adapter imports and verifies the promoted control-resolution and exclusion contract. | Learning/control unit and SQLite handoff tests pass. |
| C004 -> C006 | The Claude adapter imports and verifies the promoted control-resolution and exclusion contract. | Learning/control unit and SQLite handoff tests pass. |
| C004 -> C007 | Export, restore, deletion cleanup, and recovery consume actual learner/control state producers. | Learning/control persistence and snapshot contracts pass. |
| C004 -> C008 | Product surface exposes promoted learner state and controls. | Learning/control tests pass in integration. |
| C005 -> C008 | End-to-end behavior consumes the real Codex adapter. | Codex contract and live feasibility checks pass or an explicit read-only capability limit is recorded. |
| C006 -> C008 | End-to-end behavior consumes the real Claude adapter. | Claude contract and live feasibility checks pass or an explicit read-only capability limit is recorded. |
| C007 -> C008 | Final acceptance consumes export/delete/reliability behavior. | Ownership and failure-path tests pass in integration. |

## Capacity Waves

1. C001 implements first.
2. C002 starts after C001 promotion.
3. C003 starts after C002 promotion.
4. C004 starts after C002 and C003 promotion.
5. C005, C006, and C007 may implement concurrently after C004 promotion.
6. C008 implements after C004-C007 promotion.

Planning may use up to four component owners concurrently. Each component retains one distinct owner identity for planning, implementation, correction, and promotion.

## Allocation Packet V2 Review

Component responsibilities, public contracts, expected tests, shared-file ownership, exclusions, prefixes, branches, worktrees, and stable owners remain as approved in Packet V1 and as listed above. The only allocation change is adding C004 as an implementation prerequisite for C005, C006, and C007, moving those three components from wave 4 to wave 5 and C008 from wave 5 to wave 6. This change follows the completed tasks: each consumer requires actual promoted control or learner-state producers for local verification.

The user explicitly approved Packet V2 on 2026-09-14. The graph above is authoritative.

## Integration Test Plan

- Integration command: `pytest tests/integration`
- End-to-end command: `pytest tests/e2e`
- Static commands: `ruff check .` and `mypy src tests`
- Smoke command: `python -m expertiseos --health`
- Every handoff test creates or obtains the actual producer output and passes that same object, record, or event to the consumer in the same test. Synthetic replacements at the boundary are forbidden.
- Commands may be narrowed during early promotions only when the complete affected edge set, current end-to-end scenarios, and smoke path still run; the final gate runs all commands above.

## Edge Work Packets

### E01: C001 -> C002

- Contract: actual normalized host decision observations, explicit `KnowledgeBackend` methods, package entrypoints, and deterministic fakes feed consent lifecycle and commits.
- Invariants: required fields, actual-user provenance, canonical `operation_id`, exact versions, no unapproved fake data.
- Glue: integration owns only fixture construction and shared error/result mapping.
- Handoff test: `tests/integration/test_consent_foundation_handoff.py` passes actual C001 fake host/backend outputs through C002 proposal, grant, commit, and exact read-back.
- End-to-end coverage: `tests/e2e/test_acceptance_consent.py` AT-04 through AT-06.
- Promotion: C001 local checks, this handoff, current end-to-end tests, static checks, and smoke all pass on integration.

### E02: C002 -> C003

- Contract: guarded committed objects, versions, provenance, relationships, and operation replay feed the real backend adapter and retrieval.
- Invariants: only committed content is indexed; the exact committed object is retrieved; stale or divergent replay does not mutate.
- Glue: map canonical domain commands to the C003 adapter without exposing a host-facing backend writer.
- Handoff test: `tests/integration/test_authorized_backend_retrieval_handoff.py` commits through C002 and passes the resulting actual object to C003 read/search/fallback paths.
- End-to-end coverage: `tests/e2e/test_acceptance_consent.py` AT-04 and `tests/e2e/test_acceptance_reliability.py` AT-13.
- Promotion: C003 local checks plus the E01-E02 handoffs, affected end-to-end tests, static checks, and smoke pass.

### E03: C002 -> C004

- Contract: approved mutation envelope, receipt identity, base SQLite migration, and expected state version feed evidence/control persistence.
- Invariants: no evidence or control mutation without a matching approval receipt; duplicate `operation_id` is exact or conflicting; save alone does not advance mastery.
- Glue: integration applies the reconciled C004 schema request through C002-owned `state/sqlite.py`.
- Handoff test: `tests/integration/test_approved_learning_state_handoff.py` passes an actual C002-approved evidence/control operation into C004 persistence and summary.
- End-to-end coverage: `tests/e2e/test_acceptance_learning_controls.py` AT-07 and AT-09 through AT-11.
- Promotion: C004 local checks and E03 plus prerequisite handoffs, affected end-to-end tests, static checks, and smoke pass.

### E04: C003 -> C004

- Contract: actual approved object ID/version/scope and contradiction facts feed evidence validation and learner-state inspection.
- Invariants: version/scope mismatch stays historical but cannot justify advancement; contradiction blocks autonomy; retrieval never creates evidence.
- Glue: learner-state enrichment joins by stable ID/version without changing canonical knowledge.
- Handoff test: `tests/integration/test_retrieval_learning_handoff.py` retrieves an actual C003 object and passes its facts to C004 validation, summary, and inspection.
- End-to-end coverage: `tests/e2e/test_acceptance_learning_controls.py` AT-08 and AT-09.
- Promotion: C004 promotion requires E03 and E04 together plus affected end-to-end, static, and smoke checks.

### E05: C004 -> C005

- Contract: actual control resolution, exclusions, and learner-state projection feed the Codex adapter.
- Invariants: pause/fatigue block observation and prompts but permit approved recall; target blocks exercises only; disable blocks all expertiseOS recall.
- Glue: translate C004 booleans/reasons into Codex adapter decisions without recreating precedence.
- Handoff test: `tests/integration/test_codex_control_handoff.py` passes actual C004 resolutions through C005 event/checkpoint/source-forwarding behavior.
- End-to-end coverage: `tests/e2e/test_acceptance_codex.py` AT-01, AT-03, AT-06, and AT-11.
- Promotion: C005 local and pinned-host gates plus E05, affected end-to-end, static, and smoke checks pass.

### E06: C004 -> C006

- Contract: actual control resolution, exclusions, and learner-state projection feed the Claude Code adapter.
- Invariants: identical control semantics to E05; no host-specific weakening or duplicated domain logic.
- Glue: translate C004 outputs into Claude adapter decisions only.
- Handoff test: `tests/integration/test_claude_control_handoff.py` passes actual C004 resolutions through C006 behavior.
- End-to-end coverage: `tests/e2e/test_acceptance_claude.py` AT-01, AT-03, AT-06, and AT-11.
- Promotion: C006 local and pinned-host gates plus E06, affected end-to-end, static, and smoke checks pass.

### E07: C004 -> C007

- Contract: approved evidence, thresholds, controls, progress, exclusions, and deferred references feed export, restore, deletion cleanup, and recovery.
- Invariants: snapshots contain approved state only; restored references resolve; deletion removes selected excerpts/deferred references; recovery contains no candidate text.
- Glue: C002-owned SQLite adapter supplies the reconciled snapshot/restore/delete producer methods.
- Handoff test: `tests/integration/test_learning_export_handoff.py` exports actual C004 persisted state and restores/deletes it through C007.
- End-to-end coverage: `tests/e2e/test_acceptance_reliability.py` AT-05, AT-13, and AT-14.
- Promotion: C007 local checks plus E07 and prerequisite backend handoffs, affected end-to-end, static, benchmark, offline, and smoke checks pass.

### E08: C004 -> C008

- Contract: learner summaries, supporting evidence, effective controls, and approved mutation results feed the product tool surface and shared behavior.
- Invariants: only `pass` contributes to numeric thresholds; no direct mastery setter; deferred work is foreground-only when active.
- Glue: map C004 results to bounded C008 `ToolResult` values without semantic reinterpretation.
- Handoff test: `tests/integration/test_learning_tool_surface_handoff.py` passes actual C004 results through C008 inspection and behavior decisions.
- End-to-end coverage: `tests/e2e/test_acceptance_learning_controls.py` AT-07 through AT-11.
- Promotion: C008 requires E08 plus all remaining incoming edges and full final gates.

### E09: C005 -> C008

- Contract: actual Codex normalized events, decision observations, capability evidence, and failure outcomes feed the shared service/skill.
- Invariants: only proven actual-user events can register decisions; no prompt interrupts atomic work; unsupported write capability is false.
- Glue: register the Codex adapter with the common service and shared skill reference.
- Handoff test: `tests/integration/test_codex_product_handoff.py` passes actual C005 events and capability results into C008 service behavior.
- End-to-end coverage: `tests/e2e/test_acceptance_codex.py` and `tests/e2e/test_acceptance_cross_host.py`.
- Promotion: C008 final gate includes pinned Codex fixtures or records a P0 blocker; read-only fallback is not a write-capable pass.

### E10: C006 -> C008

- Contract: actual Claude normalized events, decision observations, capability evidence, and failure outcomes feed the shared service/skill.
- Invariants: same as E09 with Claude-specific parsing isolated in C006.
- Glue: register the Claude adapter with the common service and shared skill reference.
- Handoff test: `tests/integration/test_claude_product_handoff.py` passes actual C006 outputs into C008 service behavior.
- End-to-end coverage: `tests/e2e/test_acceptance_claude.py` and `tests/e2e/test_acceptance_cross_host.py`.
- Promotion: C008 final gate includes pinned Claude fixtures or records a P0 blocker; read-only fallback is not a write-capable pass.

### E11: C007 -> C008

- Contract: trusted export/restore selections, delete/uninstall plans, recovery, search health, persistence audits, and benchmark results feed product commands and acceptance evidence.
- Invariants: model assertions cannot authorize; `committed` alone renders Saved; degraded/unavailable stay distinct; exported/audit evidence excludes candidate content.
- Glue: map C007 result types to C008 tools and health without exposing backend or SQLite handles.
- Handoff test: `tests/integration/test_reliability_product_handoff.py` passes actual C007 results and actual C003 keyword fallback output through C008.
- End-to-end coverage: `tests/e2e/test_acceptance_reliability.py` AT-13 through AT-16.
- Promotion: C008 and final initiative gates require E08-E11, full integration/end-to-end/static/smoke commands, and the machine-validated coverage manifest.
