# Bootstrap Verification

**Intent**: Record the repeatable package, static-analysis, deterministic, and external verification results used for the G0 candidate.

Environment: macOS `15.1.1` build `24B91`, `arm64`; Python `3.12.10`; captured `2026-09-14`.

| Command | Result |
|---|---|
| `.venv-arm64/bin/ruff format --check src tests` | Exit `0`; 20 files formatted |
| `.venv-arm64/bin/ruff check src tests` | Exit `0`; all checks passed |
| `.venv-arm64/bin/mypy src tests` | Exit `0`; no issues in 20 source files |
| `.venv-arm64/bin/python -c 'import expertiseos'` | Exit `0` |
| `.venv-arm64/bin/python -m expertiseos` | Exit `0`; `{"service": "expertiseos", "status": "bootstrap-ready"}` |
| `.venv-arm64/bin/python -m pytest -q tests/unit tests/integration/test_host_feasibility.py tests/integration/test_no_write_without_user_event.py tests/integration/test_service_failure_continuity.py tests/integration/test_downstream_bootstrap.py` | Exit `0`; 37 passed |
| `.venv-arm64/bin/python -m pytest -q` | Exit `0`; 39 passed in 27.79s |
| `git diff --check` | Exit `0` |

The ARM environment was populated from `pyproject.toml` and `uv.lock` with the `g0` extra and prereleases enabled because Basic Memory pins `fastmcp==4.0.0b1`. The package has no runtime dependency on Basic Memory; external feasibility tests skip when that optional executable is absent. Deterministic host/backend contracts and downstream smoke tests require no live host, network, database setup, or model-provider key.

Result: `pass` for the bootstrap verification surface.
