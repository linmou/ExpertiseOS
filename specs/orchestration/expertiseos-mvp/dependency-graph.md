# expertiseOS MVP Dependency Graph

**Intent**: Control component ownership, contracts, dependencies, implementation waves, and integration handoffs for the MVP.

## Baseline

- Target branch: `main`
- Baseline commit: `4213d8bd6b21448401f9aba9a10208303672c7c6`
- Branch numbering: sequential, three-digit prefixes
- Integration branch: `integration/expertiseos-mvp`
- Integration worktree: `/Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration`
- Graph status: provisional until all component planning packages pass reconciliation

## Components

| ID | Branch | Worktree | Stable owner | Responsibility | Specification artifacts |
|---|---|---|---|---|---|
| C001 | `001-feasibility-bootstrap` | `../feasibility-bootstrap` | `owner-feasibility` | G0 feasibility, package bootstrap, host/backend contracts, test fakes | `specs/001-feasibility-bootstrap/` |
| C002 | `002-consent-core` | `../consent-core` | `owner-consent` | Domain models, volatile candidates, grants, approval gate, exact writes, approval state | `specs/002-consent-core/` |
| C003 | `003-backend-retrieval` | `../backend-retrieval` | `owner-backend` | Basic Memory mapping, approved retrieval, provenance, relationships, keyword fallback | `specs/003-backend-retrieval/` |
| C004 | `004-learning-controls` | `../learning-controls` | `owner-learning` | Learner evidence, mastery, target/effort controls, pause/fatigue/disable, deferred learning | `specs/004-learning-controls/` |
| C005 | `005-codex-host` | `../codex-host` | `owner-codex` | Codex onboarding, event normalization, safe checkpoints, validated decisions | `specs/005-codex-host/` |
| C006 | `006-claude-host` | `../claude-host` | `owner-claude` | Claude Code onboarding, event normalization, safe checkpoints, validated decisions | `specs/006-claude-host/` |
| C007 | `007-ownership-reliability` | `../ownership-reliability` | `owner-reliability` | Export/restore/delete/uninstall, recovery, degradation, security, performance | `specs/007-ownership-reliability/` |
| C008 | `008-product-integration` | `../product-integration` | `owner-product` | Shared behavior skill, service/MCP surface, cross-host scenarios, AT-01 through AT-16 | `specs/008-product-integration/` |

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

## Provisional Dependencies

| Prerequisite -> consumer | Reason | Provisional promotion condition |
|---|---|---|
| C001 -> C002 | Consent code needs frozen host/backend contracts, package layout, and fakes. | G0 contract tests and feasibility evidence pass in integration. |
| C002 -> C003 | Backend mutations and retrieval must expose only approved objects through guarded services. | Consent negative-path and exact-write tests pass in integration. |
| C002 -> C004 | Durable evidence and controls must use the same authorization semantics. | Approval and state contracts pass in integration. |
| C002 -> C005 | Codex decisions must register grants against the canonical proposal contract. | Approval contract is promoted. |
| C002 -> C006 | Claude decisions must register grants against the canonical proposal contract. | Approval contract is promoted. |
| C002 -> C007 | Export, deletion, and recovery operate on canonical approved state. | Approval/state contracts are promoted. |
| C003 -> C004 | Learning inspection and exclusions consume canonical retrieval results. | Retrieval contract is promoted. |
| C003 -> C005 | Codex recall and degradation reporting consume real retrieval behavior. | Backend round-trip and fallback tests pass. |
| C003 -> C006 | Claude recall and degradation reporting consume real retrieval behavior. | Backend round-trip and fallback tests pass. |
| C003 -> C007 | Export/delete/index repair require the real backend contract. | Backend lifecycle tests pass. |
| C004 -> C008 | Product surface exposes learner state and controls. | Learning/control tests pass in integration. |
| C005 -> C008 | End-to-end behavior consumes the real Codex adapter. | Codex contract and live feasibility checks pass or an explicit read-only capability limit is recorded. |
| C006 -> C008 | End-to-end behavior consumes the real Claude adapter. | Claude contract and live feasibility checks pass or an explicit read-only capability limit is recorded. |
| C007 -> C008 | Final acceptance consumes export/delete/reliability behavior. | Ownership and failure-path tests pass in integration. |

## Capacity Waves

1. C001 planning, then implementation after all planning gates pass.
2. C002 becomes implementation-ready only after C001 promotion.
3. C003 becomes implementation-ready only after C002 promotion.
4. C004, C005, C006, and C007 may implement concurrently after C002 and C003 promotion.
5. C008 implements after C004-C007 promotion.

Planning may use up to four component owners concurrently. Each component retains one distinct owner identity for planning, implementation, correction, and promotion.

## Pending Reconciliation

The authoritative DAG and edge work packets will replace this provisional section only after all eight complete planning packages pass analysis and cross-component reconciliation. Any change to approved scope, public contracts, shared-file ownership, dependencies, or waves requires renewed human allocation approval.
