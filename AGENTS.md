# backend-retrieval Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-09-14

## Active Technologies

- Python 3.12 + G0-pinned Basic Memory release; Python standard library where practical; no remote embedding or reranking service (003-backend-retrieval)

## Project Structure

```text
src/
tests/
```

## Commands

- `pytest`
- `mypy src/expertiseos`
- Use the lint command established by C001; do not add another linter.

## Code Style

Python 3.12: Follow standard conventions

## Recent Changes

- 003-backend-retrieval: Added Python 3.12 + G0-pinned Basic Memory release; Python standard library where practical; no remote embedding or reranking service

<!-- MANUAL ADDITIONS START -->
- Basic Memory API use must match C001 feasibility evidence; do not guess or use private tables.
- C003 changes to `knowledge/backend.py` and `knowledge/service.py` require integration reconciliation with C001/C002 ownership.
<!-- MANUAL ADDITIONS END -->
