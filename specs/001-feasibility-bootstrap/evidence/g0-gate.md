# G0 Candidate Gate

**Intent**: Bind the final verification results to the exact committed implementation candidate.

- Candidate SHA: `c3e885d48c12c67126c4c4ca70bd7ce8755f3d19`
- Branch: `001-feasibility-bootstrap`
- Environment: macOS `15.1.1` build `24B91`, `arm64`; Python `3.12.10`
- External components: Codex CLI `0.146.1`, Claude Code `2.1.241`, Basic Memory `0.23.2`
- Verified: `2026-09-14`

The worktree was clean at the candidate SHA before verification.

| Command | Exit | Evidence |
|---|---:|---|
| `.venv-arm64/bin/ruff format --check src tests` | 0 | 20 files already formatted |
| `.venv-arm64/bin/ruff check src tests` | 0 | All checks passed |
| `.venv-arm64/bin/mypy src tests` | 0 | No issues in 20 source files |
| `.venv-arm64/bin/python -c 'import expertiseos'` | 0 | Import succeeded |
| `.venv-arm64/bin/python -m expertiseos` | 0 | Bootstrap-ready JSON emitted |
| `.venv-arm64/bin/python -m pytest -q tests/unit tests/integration/test_host_feasibility.py tests/integration/test_no_write_without_user_event.py tests/integration/test_service_failure_continuity.py tests/integration/test_downstream_bootstrap.py` | 0 | 37 passed in 0.03s |
| `.venv-arm64/bin/python -m pytest -q` | 0 | 39 passed in 27.34s |
| `git diff --check` | 0 | No whitespace errors |

Result: `pass`. These results verify the committed candidate; the host and backend compatibility limits remain as classified in their evidence records.
