# claude-host Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-09-14

## Active Technologies

- Python 3.12 + Python standard library plus only the Claude Code integration mechanism/version proven and pinned by C001 G0; no new model or network service (006-claude-host)

## Project Structure

```text
src/
tests/
```

## Commands

```bash
pytest
ruff check .
mypy src/expertiseos/hosts/claude_code.py tests/contract/test_claude_code_adapter.py tests/integration/test_claude_code_service.py
```

## Code Style

Python 3.12: Follow standard conventions

## Recent Changes

- 006-claude-host: Added Python 3.12 + Python standard library plus only the Claude Code integration mechanism/version proven and pinned by C001 G0; no new model or network service

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
