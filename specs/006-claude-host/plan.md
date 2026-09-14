# Implementation Plan: Claude Code Host Adapter

**Intent**: Plan the smallest evidence-gated Claude Code translation layer that preserves shared consent, controls, retrieval, and failure semantics.

**Branch**: `006-claude-host` | **Date**: 2026-09-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/006-claude-host/spec.md`

## Summary

Implement a thin Claude Code adapter in `src/expertiseos/hosts/claude_code.py`. It translates only G0-proven public host events into C001's normalized contract, validates actual-user decisions against an active binding before invoking C002, consumes C003 retrieval and C004 control/exclusion results, and treats all expertiseOS failures as non-blocking for ordinary Claude work. Exact registration, event names, host version, OS, permission mode, and session identity come from passed C001 feasibility evidence; missing proof produces explicit unavailable capabilities and `can_write=false`.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Python standard library plus only the Claude Code integration mechanism/version proven and pinned by C001 G0; no new model or network service
**Storage**: None owned by the adapter; volatile per-session state only, with all durable operations delegated to the shared local service
**Testing**: pytest, Ruff, mypy; sanitized recorded contract fixtures plus a reproducible pinned live-host check
**Target Platform**: Only the Claude Code version, OS, registration mechanism, and permission mode that pass C001 G0
**Project Type**: One installable local Python package with one shared local service process
**Performance Goals**: Constant-time event normalization and no model call per low-level event; component checks also preserve the project lifecycle bookkeeping p95 target below 200 ms
**Constraints**: Real-user event proof is mandatory for writes; public supported host interfaces only; no candidate persistence; no direct backend/SQLite access; host work continues on failures
**Scale/Scope**: One local user, one adapter instance per active Claude session, bounded retrieval of at most 20 approved records

## Constitution Check

*GATE: Passed before research and rechecked after design.*

| Principle | Plan Evidence | Result |
|---|---|---|
| Explicit Approval Before Persistence | Actual-user fixture plus exact `DecisionBinding` validation; adapter only emits a `DecisionObservation`; C002 remains the grant/commit owner | PASS |
| Work Continues, Unsafe Writes Stop | Every adapter-to-service call has a typed no-op/degraded path for host work and no non-committed result is rendered as Saved | PASS |
| Local, Minimal, Inspectable State | One adapter module, volatile session values, sanitized fixture metadata, and the existing local service; no new durable store or service | PASS |
| Permission, Knowledge, Evidence, Mastery Stay Separate | Host events never create mastery; retrieval stays untrusted; proposal decisions remain separate from task and learning outcomes | PASS |
| Contracts and Verification Drive Delivery | C001-C004 boundaries are named in tasks; contract, integration, live-host, static, and smoke gates are required | PASS |

Post-design recheck: PASS. The data model contains only adapter-owned volatile/evidence values, and the public contract delegates every domain decision to its upstream owner.

## Project Structure

### Documentation (This Feature)

```text
specs/006-claude-host/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── claude-host-adapter.md
├── checklists/
│   └── requirements.md
├── implementation-evidence.md  # created during implementation, not planning
└── tasks.md
```

### Source Code (Repository Root)

```text
src/expertiseos/hosts/
├── contract.py                 # C001-owned upstream contract
└── claude_code.py              # C006-owned adapter and host setup translation

tests/
├── fixtures/claude_code/       # sanitized, versioned host event/evidence fixtures
├── contract/test_claude_code_adapter.py
├── integration/test_claude_code_service.py
└── e2e/test_claude_code_live.py
```

**Structure Decision**: Keep Claude event parsing, session normalization, capability mapping, decision matching, and Claude-specific install/remove translation in one adapter module. Split it only if implementation evidence shows an independently owned concern. C008 owns shared behavioral skill and cross-host wiring; integration owns shared compatibility documentation.

## Dependency Gates

1. C001 integration must provide the exact `HostAdapter`, host values, evidence schema, and a passed Claude G0 capability record.
2. C002 integration must provide proposal expiry, user-decision registration, and truthful commit results.
3. C003 integration must provide bounded health-labeled retrieval through the service layer.
4. C004 integration must provide resolved controls and literal scope-exclusion matching.
5. C006 implementation may begin against integrated upstream contracts only after integration publishes the corresponding promotion SHA.
6. If C001 cannot prove actual-user decision capture for the selected environment, read/search may proceed where proven, but the write-capable acceptance path remains blocked and `can_write=false`.

## Implementation Sequence

1. Import and pin the integrated upstream contract shapes; add sanitized evidence fixtures for the exact supported Claude environment.
2. Implement session lifecycle and raw-to-normalized event translation with conservative atomic-depth checkpoint eligibility.
3. Add control/exclusion gating before source forwarding and bounded service retrieval.
4. Implement deterministic Save/Edit/Skip observation against one active exact binding; delegate proposal lifecycle and grants to C002.
5. Add setup/remove translation that preserves unrelated Claude configuration and reports independent capabilities.
6. Add failure boundaries around service calls so host task callbacks always return control without false mutation success.
7. Run contract and integration checks, then the pinned live-host fixture and static/smoke gates; record commands, metadata, results, and precise unsupported limits in `specs/006-claude-host/implementation-evidence.md` for integration review.

## Complexity Tracking

No constitution violations or additional architectural layers are planned.
