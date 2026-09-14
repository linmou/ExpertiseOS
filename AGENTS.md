# ownership-reliability Development Guidelines

**Intent**: Keep C007 implementation aligned with its local Python stack, owned paths, and verification commands.

Auto-generated from all feature plans. Last updated: 2026-09-14

## Active Technologies

- Python 3.12, standard library, and the C001-pinned Basic Memory adapter behind C003's `KnowledgeBackend` contract (007-ownership-reliability)

## Project Structure

```text
src/
tests/
```

## Commands

`pytest`, `mypy src/expertiseos/ownership.py src/expertiseos/reliability.py src/expertiseos/security.py benchmarks/benchmark_mvp.py`, and `ruff check .`

## Code Style

Python 3.12: Follow standard conventions

## Recent Changes

- 007-ownership-reliability: Added Python 3.12 with local approved-state, backend, and learner/control contracts.

<!-- MANUAL ADDITIONS START -->
- Implement from `specs/007-ownership-reliability/tasks.md` with its verification steps; do not activate the strict fast-multi-agent TDD workflow.
- Use `apply_patch` for text edits and prefix shell commands with `rtk`.
- C007 owns `src/expertiseos/ownership.py`, `src/expertiseos/reliability.py`, `src/expertiseos/security.py`, its tests, and benchmark. Do not edit shared `state/sqlite.py`, `knowledge/service.py`, service/MCP wiring, skill, or host adapters.
- Every new Python/test file starts with a shebang and a purpose comment. Dataclasses declare all fields without defaults.
- Keep operation/repair records content-free. Never recover candidates or unused grants.
<!-- MANUAL ADDITIONS END -->
