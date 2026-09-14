# learning-controls Development Guidelines

Intent: Keep implementation of C004 aligned with its approved Python, SQLite, and verification boundaries.

Auto-generated from all feature plans. Last updated: 2026-09-14

## Active Technologies

- Python 3.12 + Python standard library plus the project contracts established by C001-C003; no new runtime dependency (004-learning-controls)

## Project Structure

```text
src/
tests/
```

## Commands

```bash
pytest tests/unit tests/contract tests/integration/test_learning_state_sqlite.py
mypy src/expertiseos/learning tests/unit tests/contract tests/integration/test_learning_state_sqlite.py
ruff check src/expertiseos/learning tests/unit tests/contract tests/integration/test_learning_state_sqlite.py
```

## Code Style

Python 3.12: Follow standard conventions

## Recent Changes

- 004-learning-controls: Added Python 3.12 + Python standard library plus the project contracts established by C001-C003; no new runtime dependency

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
