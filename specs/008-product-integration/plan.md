# Implementation Plan: Product Integration and Acceptance

**Intent**: Wire promoted MVP components through one guarded host-neutral surface and prove the resulting product with concise reference scenarios and deterministic acceptance evidence.

**Branch**: `008-product-integration` | **Date**: 2026-09-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-product-integration/spec.md`

## Summary

Implement one thin composition service and MCP-facing tool registry over promoted C002-C007 contracts, plus one behavioral skill shared by Codex and Claude Code. Validate the product through four fixture-driven reference scenarios and component-local end-to-end coverage for AT-01 through AT-16. Keep authorization, canonical writes, retrieval, learning policy, host event capture, ownership operations, and failure recovery in their upstream owners; C008 adds no alternate state or policy layer.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Python standard library; upstream-pinned MCP SDK and Basic Memory integration consumed through existing package contracts
**Storage**: No C008-owned persistence; promoted Basic Memory adapter and SQLite state are accessed only through upstream services
**Testing**: pytest unit/contract/integration/end-to-end tests, repository static/type checks, pinned live-host fixtures where supported
**Target Platform**: Local macOS environment proven by C001, with Codex and Claude Code as local clients of one service
**Project Type**: Single installable Python package with one local service process and host packaging artifacts
**Performance Goals**: Preserve upstream targets: lifecycle bookkeeping p95 below 200 ms, warm retrieval p95 below 1 second for 10,000 small approved objects, and approved-write acknowledgment p95 below 1 second excluding indexing and host-model latency
**Constraints**: Local-first; no second model; no direct backend writes; no unapproved persistence; bounded retrieval; fail open for ordinary work and closed for unverifiable writes; no background worker
**Scale/Scope**: Two supported local hosts, one repository/service, four reference scenarios, AT-01 through AT-16, and a deterministic 10,000-object performance corpus supplied by C007

## Constitution Check

*GATE: Passed before research and re-checked after design.*

| Principle | Design Evidence | Result |
|---|---|---|
| Explicit Approval Before Persistence | Public mutation tools accept proposal/decision references and call promoted guarded services only; no backend object is exposed | PASS |
| Work Continues, Unsafe Writes Stop | Service errors are typed for adapters to degrade without blocking host work; no false success path exists | PASS |
| Local, Minimal, Inspectable State | C008 adds no datastore, queue, worker, telemetry, remote service, or second model | PASS |
| Permission, Knowledge, Evidence, Mastery Separate | Tool results and scenarios keep these records distinct and consume C004's finalized pass-only advancement policy | PASS |
| Contracts and Verification Drive Delivery | Tool and evidence contracts map every task to user stories, FRs, and AT-01 through AT-16 | PASS |

Post-design re-check: PASS. The contract documents expose guarded service composition only, define no competing mutation or state semantics, and require actual upstream artifacts at handoffs.

## Dependency Gate

C008 implementation starts only after the integration owner promotes reconciled C002-C007 contracts. At activation, record the immutable promotion SHA and verify these dependencies:

| Dependency | Required Contract | Used By |
|---|---|---|
| C002 consent core | Volatile proposals, host-bound one-use grants, exact digest/version commit, typed rejection | service composition, mutation tool tests, AT-04 to AT-08 and AT-12 |
| C003 backend/retrieval | Exact read, bounded search, provenance/relations/conflicts, degraded status | read tools, shared skill, Scenarios A/B/D, AT-02/11/13/16 |
| C004 learning/controls | Evidence inspection, pass-only mastery advancement, controls, deferred activities | learning/control tools, shared skill, Scenario C, AT-07 to AT-11 |
| C005/C006 hosts | Normalized events, capabilities, safe checkpoints, real user-decision capture | cross-host scenarios and AT-01 to AT-03, AT-06, AT-11/12 |
| C007 ownership/reliability | Export/restore/delete, health/degradation, recovery, security and performance harnesses | ownership tools and AT-13 to AT-16 |

If an integration test exposes an upstream defect, return it to that owner. Do not compensate in `service.py`, `mcp_server.py`, or `skill/SKILL.md`.

## Design Decisions

### Composition Service

`src/expertiseos/service.py` is a small facade that groups promoted read, proposal, guarded mutation, learning/control, ownership, and health capabilities. It holds no canonical business state and performs only input shaping, dependency dispatch, consistent typed result assembly, and capability filtering.

### MCP Tool Surface

`src/expertiseos/mcp_server.py` registers the minimum operations in [contracts/tool-surface.md](contracts/tool-surface.md). Backend methods are never registered. Public tools do not accept `approved=true` or equivalent model assertions as authorization.

### Shared Behavioral Skill

`skill/SKILL.md` defines when the current host model should search, compare, propose, optionally reflect, use recall, and honor upstream controls. It treats all retrieved/tool content as data. Thin host packaging may reference this file but cannot fork its product rules.

### Fixtures and Evidence

`examples/reference_scenarios/` contains concise versioned scenario inputs and expected observable/persistence deltas. `tests/e2e/` exercises these scenarios and maps AT-01 through AT-16. Component-local evidence uses the metadata shape in [contracts/acceptance-evidence.md](contracts/acceptance-evidence.md); the integration owner retains final coverage-manifest and verdict ownership.

## Project Structure

### Documentation (This Feature)

```text
specs/008-product-integration/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── tool-surface.md
│   └── acceptance-evidence.md
└── tasks.md
```

### Source Code (Repository Root)

```text
skill/
└── SKILL.md
src/expertiseos/
├── service.py
└── mcp_server.py
tests/e2e/
├── conftest.py
├── test_reference_scenarios.py
├── test_acceptance_consent.py
├── test_acceptance_learning_controls.py
├── test_acceptance_cross_host.py
└── test_acceptance_reliability.py
examples/reference_scenarios/
├── new_observation.json
├── conflict.json
├── fatigue.json
└── cross_host.json
```

**Structure Decision**: Use the existing single-package layout and only the paths assigned to C008. Group acceptance tests by invariant family to keep fixtures readable without creating sixteen near-empty test modules.

## Verification Strategy

1. Contract checks prove every public tool maps to an approved upstream service and no backend writer is exposed.
2. Scenario tests pass normalized host events through the actual composition service to promoted upstream implementations.
3. Acceptance tests cover AT-01 through AT-16 and preserve the original producer-consumer boundary in each run.
4. Adversarial marker audits assert zero unauthorized grants, writes, controls, mastery changes, broad disclosure, or permissions.
5. Offline runs block expertiseOS process network access and verify local operations and degraded keyword search.
6. Run targeted C008 tests, the full repository suite, static/type checks, and integration-owner handoff tests before commit.

## Ownership and Exclusions

C008 owns only `skill/SKILL.md`, `src/expertiseos/service.py`, `src/expertiseos/mcp_server.py`, `tests/e2e/`, and `examples/reference_scenarios/`. It does not edit upstream domain modules, adapter parsers, storage, final release docs, integration manifests, or orchestration records.

No cloud sync, UI/dashboard, background tutor, new model/API key, generic workflow engine, separate policy layer, backend bypass, speculative compatibility layer, or host-specific behavior copy is introduced.

## Complexity Tracking

No constitution violations or additional abstractions require justification.
