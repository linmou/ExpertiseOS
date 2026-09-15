# C005 Component Verification

**Intent**: Record the complete reproducible verification result for the Codex adapter package.

Environment: Python `3.12.7`; Codex CLI `0.146.1`; Darwin `24.1.0`, `arm64`; date `2026-09-14`.

| Command | Result | Exit |
|---|---|---|
| `.venv/bin/python -m pytest -q` | `229 passed, 3 skipped in 2.28s`; skips are optional Basic Memory G0 dependency tests | 0 |
| `.venv/bin/ruff check .` | `All checks passed!` | 0 |
| `.venv/bin/ruff format --check .` | `90 files already formatted` | 0 |
| `.venv/bin/mypy` | `Success: no issues found in 90 source files` | 0 |
| `.venv/bin/python -c 'from expertiseos.hosts.codex import CodexAdapter, capabilities_for, normalize_hook; print("codex import smoke: ok")'` | `codex import smoke: ok` | 0 |
| `.venv/bin/python -m expertiseos` | `{"service": "expertiseos", "status": "bootstrap-ready"}` | 0 |

No GPU task, external host mutation, plugin installation, user configuration edit, or persistent Codex write was performed.
