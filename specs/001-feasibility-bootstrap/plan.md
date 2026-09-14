# Implementation Plan: Feasibility and Repository Bootstrap

**Intent**: Turn the G0 requirements into a minimal executable feasibility gate and stable downstream contracts.

**Branch**: `001-feasibility-bootstrap` | **Date**: 2026-09-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-feasibility-bootstrap/spec.md`

## Summary

Prove the supported Codex, Claude Code, and Basic Memory boundaries before later components depend on them. Bootstrap one Python package with two narrow protocols, normalized immutable values, deterministic fakes, and focused contract/feasibility checks. Record evidence and capability blockers without implementing product consent, production host adapters, or production backend mapping.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Python standard library for contracts/fakes; pytest for verification; exact supported Codex, Claude Code, Basic Memory, and host integration versions selected and pinned by G0 evidence  
**Storage**: No product storage in this component; fake backend uses process memory only, and feasibility fixtures use disposable approved test data  
**Testing**: pytest unit and integration markers; mypy strict checks for owned package paths; Ruff check/format verification  
**Target Platform**: Local macOS and/or Linux combinations actually proven for pinned Codex and Claude Code releases  
**Project Type**: Installable local Python package with one development process entrypoint stub  
**Performance Goals**: Bootstrap contract checks complete in under 30 seconds excluding dependency installation and live-host manual validation  
**Constraints**: Local-first; no second model API; supported public interfaces only; no public listener; unverified write capability becomes read-only/blocked; shared documentation files are integration-owned  
**Scale/Scope**: Two hosts, one backend, two protocols, deterministic fakes, and the G0 evidence matrix only

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

| Principle | Plan evidence | Result |
|-----------|---------------|--------|
| Explicit Approval Before Persistence | Host proof distinguishes real user events and tests rejection without one; fake backend accepts approved fixtures only | PASS |
| Work Continues, Unsafe Writes Stop | Host-continuity fixture covers service failure; unsupported authorization capability is read-only/blocked | PASS |
| Local, Minimal, and Inspectable State | One package, no durable product state, two protocols, public backend interfaces, no remote model/memory dependency | PASS |
| Permission, Knowledge, Evidence, and Mastery Stay Separate | G0 contracts carry authorization-relevant facts but implement no mastery or learner state | PASS |
| Contracts and Verification Drive Delivery | Every interface operation has contract checks; live evidence is pinned and reproducible | PASS |

Post-design check: the data model and contracts add no persistent candidate path, workflow engine, production adapter, production backend mapping, or external service. No constitutional exception is required.

## Project Structure

### Documentation (this feature)

```text
specs/001-feasibility-bootstrap/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
├── contracts/
│   ├── host-adapter.md
│   └── knowledge-backend.md
└── tasks.md
```

### Source Code (repository root)

```text
pyproject.toml
src/expertiseos/
├── __init__.py
├── __main__.py
├── hosts/
│   ├── __init__.py
│   └── contract.py
└── knowledge/
    ├── __init__.py
    └── backend.py
tests/
├── fakes.py
├── unit/
│   ├── test_host_contract.py
│   └── test_backend_contract.py
├── integration/
│   ├── test_host_feasibility.py
│   ├── test_backend_feasibility.py
│   ├── test_no_write_without_user_event.py
│   ├── test_service_failure_continuity.py
│   └── test_local_backend_offline.py
└── e2e/
```

**Structure Decision**: Use the repository shape mandated by the MVP plan. `__main__.py` is only a local development process stub proving package wiring and failure isolation; integration-owned `service.py` is untouched. Feasibility evidence needed by shared documents is produced under this feature's spec directory for the integration owner to incorporate.

## Implementation Phases

### Phase 0 - External Feasibility Evidence

1. Inspect released host and backend versions and select candidate supported combinations.
2. Run reproducible activation, lifecycle, actual-user-event, safe-checkpoint, session identity, service-failure, backend round-trip, deletion, rebuild, offline, and license checks.
3. Record exact commands, environment metadata, results, and blockers in `research.md` and evidence artifacts; never mark an unexecuted check as passed.

### Phase 1 - Minimal Contracts and Bootstrap

1. Configure the installable package and verification entrypoints.
2. Implement only normalized host values/protocol and approved-data backend values/protocol in owned paths.
3. Implement deterministic fakes without persistence or host/vendor imports.
4. Add focused unit and integration fixtures that exercise contracts and replay verified G0 boundaries.
5. Supply integration-owned documentation content as evidence references, not concurrent edits.

### Phase 2 - G0 Gate

1. Run package import, format, lint, mypy, unit, integration, offline, and supported live/manual checks.
2. Confirm no production feature behavior or prohibited infrastructure entered the diff.
3. Classify each host write capability and the overall G0 result as pass, compatibility-limited, or blocked.

## Dependency and Ownership Boundaries

- This component is the root of the implementation DAG; later components consume its immutable promotion SHA.
- Public outputs: package/test commands, `HostAdapter`, `KnowledgeBackend`, normalized values, and deterministic fakes.
- Integration owner edits `README.md`, `docs/compatibility.md`, and `docs/implementation-status.md` using this component's evidence.
- Backend component may later make only narrow compatible changes to `knowledge/backend.py`; host components implement vendor adapters without changing domain semantics.
- Consent and exact-write components own proposal lifecycle, grants, approval gates, receipts, and durable mutation ordering.

## Verification Strategy

- **Unit**: protocol shape, normalized event validation, capability truthfulness, fake backend approved-input guard, expected-version conflicts, stable fake identity/order.
- **Integration**: reproducible host/backend feasibility fixtures, actual-user-event distinction, service failure continuity, supported backend round trips, delete/rebuild, and offline behavior.
- **Live/manual**: pinned Codex and Claude Code activation/config preservation/uninstall/event observations where supported automation is unavailable.
- **Static**: Ruff check/format and strict mypy over owned source and tests.
- **Gate evidence**: exact command, exit status, environment, version, timestamp, fixture, and limitation for every claimed capability.

## Complexity Tracking

No constitutional violation or additional architecture is required.
