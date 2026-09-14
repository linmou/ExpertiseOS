# expertiseOS MVP Development Guidelines

**Intent**: Keep implementation aligned with the approved component contracts, ownership boundaries, and verification gates.

Auto-generated from all feature plans. Last updated: 2026-09-14

## Active Technologies

- Python 3.12 and the standard library where practical.
- Pytest, Ruff, and strict mypy through the commands established by C001.
- Only Basic Memory and host integration versions proven and pinned by G0 evidence.
- No second generative model or remote memory, embedding, or reranking service.

## Project Structure

```text
src/
tests/
```

## Commands

Use the format, lint, mypy, import, unit, integration, end-to-end, and smoke commands defined in `pyproject.toml` and the active component's `tasks.md`. Do not invent alternate command paths.

## Code Style

Python 3.12: follow standard conventions and keep direct code paths.

Every value-object field is required at construction. Do not add dataclass defaults.

Every new Python or test file starts with a Python shebang and a purpose comment. Every new test identifies the production file and behavior it covers.

## Scope

Implement only dependency-ready tasks from the active component package under `specs/`.

- C001 owns package bootstrap, shared host/backend contracts, fakes, and feasibility evidence.
- C002 owns domain, volatile candidates, approval, guarded mutations, and base SQLite state.
- C003 owns Basic Memory mapping and retrieval; shared contract changes require reconciliation with C001/C002.
- C004 owns learning and control behavior; SQLite schema changes route through C002.
- C005 and C006 own only their respective thin host adapters and host-specific setup.
- C007 owns export, restore, deletion, recovery, reliability, security helpers, and benchmarks.
- C008 owns the shared behavior skill, service/MCP wiring, reference scenarios, and component-level end-to-end tests.
- The integration owner owns orchestration records, cross-component glue, edge tests, final acceptance, and shared release documentation.

Do not bypass the approval gate, persist unapproved candidate content, duplicate domain behavior in adapters, or add cloud/background/distributed infrastructure.

## Recent Changes

- C001-C007 planning packages reconciled into the integration branch.
- C004 mastery policy: only `pass` evidence contributes to configurable numeric thresholds; autonomous safeguards remain mandatory.

<!-- MANUAL ADDITIONS START -->
- Use task-based development and proportionate verification; do not activate strict fast-multi-agent TDD.
- Use `apply_patch` for text edits and prefix shell commands with `rtk`.
<!-- MANUAL ADDITIONS END -->
