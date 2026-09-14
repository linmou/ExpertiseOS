# expertiseOS MVP Dependency Graph

**Intent**: Control component ownership, contracts, dependencies, implementation waves, and integration handoffs for the MVP.

## Baseline

- Target branch: `main`
- Baseline commit: `4213d8bd6b21448401f9aba9a10208303672c7c6`
- Branch numbering: sequential, three-digit prefixes
- Integration branch: `integration/expertiseos-mvp`
- Integration worktree: `/Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration`
- Graph status: reconciled proposal awaiting Allocation Packet V2 approval because implementation waves changed

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

## Proposed Authoritative Dependencies

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

Human approval of Packet V2 is required before this graph becomes authoritative and before edge work packets or implementation activation are created.
