# Implementation Plan: Learner Evidence and Learning Controls

**Intent**: Implement deterministic learner-state and control behavior through the existing approval and state boundaries with no separate tutor, scheduler, or scoring system.

**Branch**: `004-learning-controls` | **Date**: 2026-09-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-learning-controls/spec.md`

## Summary

Add two host-neutral modules: `learning/evidence.py` for approved evidence validation and deterministic per-object/version/scope mastery summaries using adjustable monotonic integer pass thresholds, and `learning/controls.py` for reflection/effort accounting, control precedence, exclusions, inspection projections, and minimal deferred activities. Durable mutations use C002's approval gate and SQLite state boundary. C003 supplies approved retrieval facts and conflicts. Host adapters and C008 consume pure control decisions and bounded inspection data.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Python standard library plus the project contracts established by C001-C003; no new runtime dependency

**Storage**: Shared local SQLite `state.db` through C002-owned `src/expertiseos/state/sqlite.py`; approved object identity/version and conflict facts from C003

**Testing**: pytest unit tests with fake approval/state/retrieval ports; integration tests against the shared SQLite implementation after promotion

**Target Platform**: Local macOS/Linux process used by Codex and Claude Code adapters

**Project Type**: One installable Python package and one local service process

**Performance Goals**: Pure state/control resolution completes without I/O; bounded inspection performs one state query per view and does not scan unrelated objects

**Constraints**: No unapproved persistence; no dataclass field defaults; deterministic behavior; local device timezone periods; idempotent approved event handling; ordinary host work remains unaffected

**Scale/Scope**: One user, two local hosts, per-object/version/scope summaries, small control records and aggregate counters; no distributed coordination

## Constitution Check

*GATE: Passed before and after design.*

| Principle | Design evidence | Result |
|---|---|---|
| Explicit Approval Before Persistence | All evidence, mastery-affecting, control, exclusion, counter, and deferred mutations enter through C002's guarded mutation contract; rejected proposals never reach the state port. | PASS |
| Work Continues, Unsafe Writes Stop | Control output describes expertiseOS behavior only; storage or approval failure rejects the mutation and does not block ordinary host work. | PASS |
| Local, Minimal, and Inspectable State | Only evidence, controls, counters, exclusions, and approved-object references use shared SQLite. | PASS |
| Permission, Knowledge, Evidence, and Mastery Stay Separate | Pure summary accepts approved evidence only; save, retrieval, assistant output, unknown contribution, and self-report cannot advance mastery. | PASS |
| Contracts and Verification Drive Delivery | Every requirement maps to unit/contract/integration tests and the C002/C003/C005-C008 handoffs are explicit. | PASS |

No constitution exception or complexity justification is required.

## Project Structure

### Documentation (this feature)

```text
specs/004-learning-controls/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── verification.md
├── contracts/
│   ├── learning-controls.md
│   └── sqlite-schema-request.md
└── tasks.md
```

### Source Code (repository root)

```text
src/expertiseos/
└── learning/
    ├── evidence.py
    └── controls.py

tests/
├── contract/
│   └── test_learning_boundaries.py
├── unit/
│   ├── learning_fakes.py
│   ├── test_learner_evidence.py
│   ├── test_mastery_transitions.py
│   ├── test_autonomy_heuristic.py
│   ├── test_reflection_counting.py
│   ├── test_effort_limit.py
│   ├── test_target_vs_fatigue.py
│   ├── test_pause_disable.py
│   ├── test_deferred_learning.py
│   ├── test_scope_exclusions.py
│   └── test_inspection.py
└── integration/
    └── test_learning_state_sqlite.py
```

**Structure Decision**: Keep all owned production behavior in the existing `learning` package. C002 retains exclusive ownership of `state/sqlite.py`; this component supplies the schema contract and integration test requirements. C008 owns service/MCP wiring and shared skill behavior.

## Implementation Phases

### Phase 1 - Evidence and mastery core

Implement immutable input/result records without definition defaults, pass-only evidence eligibility, version/scope filtering, validated monotonic advancement thresholds, and a pure mastery summary. State meanings remain direct rules rather than points. Autonomous evaluation returns unmet conditions for inspection and enforces its safeguards independently of threshold values.

### Phase 2 - Controls and accounting

Implement explicit control inputs and one effective behavior result with separate permissions for observation, collection prompts, exercises, and recall. Add daily/weekly period keys, reflection qualification, effort classification, idempotency identifiers, fatigue transition intent, exclusions, and deferred-activity validation.

### Phase 3 - Persistence and handoffs

Integrate through C002's guarded mutation and SQLite ports after its promotion SHA. Validate C003 object/version/conflict input. Provide bounded inspection DTOs for C008 and control decisions for C005-C006. Do not add host parsing or public tool handlers here.

## Verification Strategy

- Unit: every learner-state meaning, pass-only contribution, valid and invalid threshold configurations, every autonomous missing-condition case, version/scope boundaries, and all prohibited evidence sources.
- Unit: all control precedence combinations, target rollover during pause/rest, explicit fatigue, effort boundaries, reflection idempotency, exclusions, and deferred-content rejection.
- Contract: exact C002 approval/state requests and C003 retrieval facts using C004-owned fixtures; no direct SQLite or backend bypass.
- Integration: actual C002 SQLite migration round-trip, restart persistence, duplicate delivery, global cross-host counts, and bounded inspection.
- Acceptance handoff: C008 exercises AT-07, AT-09, AT-10, AT-11, and the learning/control portions of AT-12 and AT-15 using the real service path.
- Static: run repository mypy and lint checks for both owned modules and tests.

## Ownership and Dependencies

| Boundary | Owner | This component action |
|---|---|---|
| Approval proposals, decision grants, receipts | C002 | Consume guarded mutation contract; never infer approval. |
| `src/expertiseos/state/sqlite.py` and migrations | C002 | Supply and test `contracts/sqlite-schema-request.md`; request changes through owner. |
| Approved object versions/conflicts/retrieval | C003 | Consume narrow identity, version, scope, and unresolved-conflict facts. |
| Host events and exclusion pre-filter | C005/C006 | Return pure control/exclusion decisions; host owners enforce before forwarding content. |
| Service/MCP, shared skill, E2E | C008 | Supply bounded DTOs and tests; integration owner wires them. |

## Complexity Tracking

No violations. The design adds no infrastructure beyond the two required learning modules and shared-state schema additions.
