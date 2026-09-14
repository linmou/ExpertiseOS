# Implementation Plan: Codex Host Adapter

**Branch**: `005-codex-host` | **Date**: 2026-09-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-codex-host/spec.md`

## Summary

Implement a thin Codex adapter and reversible onboarding path that translate only G0-verified supported Codex events into the shared HostAdapter contract. The adapter tracks minimal volatile session/checkpoint/proposal state, delegates all consent and durable behavior to upstream services, exposes evidence-backed capabilities, and never makes ordinary Codex work depend on expertiseOS availability.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Existing `expertiseos` package and upstream HostAdapter/approval/service contracts; the Codex integration dependency and API are accepted only from the G0 evidence packet
**Storage**: No candidate or grant storage; only minimal reversible installation/onboarding state through the upstream state interface if G0 proves it necessary
**Testing**: pytest contract/integration fixtures plus reproducible pinned live-Codex fixtures supplied by the verified integration surface
**Target Platform**: Exact local Codex version, operating system, installation surface, and permission mode proven by G0
**Project Type**: Thin adapter within one installable local Python package and one shared local service process
**Performance Goals**: No learning prompt during an incomplete atomic operation; no semantic analysis per low-level event; bounded startup/control load; ordinary host work unaffected by adapter/service failures
**Constraints**: Local-first; released/supported interfaces only; exact actual-user event provenance; session-scoped volatile state; false capability claims forbidden; no second model, scheduler, or unrestricted writes
**Scale/Scope**: One user's local Codex sessions connected to one shared local expertiseOS service

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Explicit approval before persistence**: PASS by design. The adapter can only register a decision from a G0-verified actual-user input event and delegates exact digest/version checks to the approval service.
- **Work continues, unsafe writes stop**: PASS by design. Adapter calls are non-owning side behavior; failures suppress expertiseOS actions and never claim a save.
- **Local, minimal, inspectable state**: PASS by design. Only per-session checkpoint/proposal references are volatile; no candidate payload is written by this component.
- **Separation of permission, knowledge, evidence, and mastery**: PASS by ownership. The adapter emits normalized facts and does not compute or mutate these domains.
- **Contracts and verification drive delivery**: PASS with implementation gate. Contract fixtures are planned; write capability cannot start until G0 supplies reproducible evidence for the exact Codex surface.

**Pre-implementation gate**: The integration owner must provide the immutable G0 evidence package described in [contracts/g0-evidence.md](contracts/g0-evidence.md), plus compatible promoted upstream contracts. Missing actual-user capture evidence forces `can_validate_user_decisions=false` and `can_write=false`; missing activation or checkpoint evidence disables only those corresponding capabilities. No private hook or inferred support may substitute.

## Project Structure

### Documentation (this feature)

```text
specs/005-codex-host/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
├── evidence/            # implementation-time commands, results, and metadata
└── tasks.md
```

### Source Code (repository root)

```text
src/expertiseos/hosts/
└── codex.py

tests/contract/
├── test_codex_host_contract.py
├── test_codex_onboarding.py
├── test_codex_user_event_binding.py
├── test_codex_safe_checkpoint.py
├── test_codex_scope_controls.py
├── test_codex_session_expiry.py
└── test_codex_capabilities.py

tests/integration/
├── test_codex_service_failure.py
└── test_codex_shared_service.py

tests/e2e/
└── test_codex_live_host.py

tests/fixtures/codex/
├── README.md
└── g0_events.json
```

**Structure Decision**: Keep Codex translation and its verified registration functions in one host module. Separate contract, service-integration, and live-host fixtures by validation layer. Shared docs, service wiring, behavioral skill, domain approval, retrieval, controls, and cross-host acceptance remain with their assigned owners.

## Complexity Tracking

No constitution violations or complexity exceptions.

## Design Outputs

- [research.md](research.md): evidence gates and bounded technical decisions.
- [data-model.md](data-model.md): volatile adapter state and normalized facts.
- [contracts/codex-adapter.md](contracts/codex-adapter.md): producer/consumer interface and invariants.
- [contracts/g0-evidence.md](contracts/g0-evidence.md): immutable feasibility inputs required before implementation.
- [quickstart.md](quickstart.md): component and pinned live-host verification sequence.

## Dependency and Promotion Order

1. Consume the integration branch SHA where C001 HostAdapter evidence/contract, C002 proposal/grant APIs, C003 retrieval/degradation, and C004 controls/exclusions are green.
2. Validate the G0 evidence packet against `contracts/g0-evidence.md`; do not implement unproven host bindings.
3. Implement contract fixtures and adapter/onboarding behavior using only the promoted contracts.
4. Run unit/contract, integration failure, static/type, and pinned live-host checks.
5. Commit evidence and return the component SHA to integration; C008 owns shared behavioral skill and cross-host wiring.

## Post-Design Constitution Check

PASS. The design adds no durable candidate path, authorization shortcut, domain duplication, new service, background process, or speculative compatibility. Every write-capable path remains conditional on exact actual-user evidence and the upstream approval gate.
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
