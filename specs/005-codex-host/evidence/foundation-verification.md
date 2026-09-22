# Codex Foundation Verification

**Intent**: Record normalized-event, capability, and type-safety evidence for the thin adapter.

Environment: Python `3.12.7`; Codex CLI `0.146.1`; Darwin `24.1.0`, `arm64`; date `2026-09-14`.

```text
.venv/bin/python -m pytest -q tests/contract/test_codex_host_contract.py tests/contract/test_codex_capabilities.py tests/contract/test_codex_onboarding.py tests/contract/test_codex_safe_checkpoint.py tests/contract/test_codex_scope_controls.py tests/contract/test_codex_user_event_binding.py tests/contract/test_codex_session_expiry.py tests/integration/test_codex_service_failure.py tests/integration/test_codex_shared_service.py tests/e2e/test_codex_live_host.py
..................................... [100%]
37 passed in 0.11s
exit: 0
```

```text
.venv/bin/mypy src/expertiseos/hosts/codex.py tests/contract/test_codex_*.py tests/integration/test_codex_*.py tests/e2e/test_codex_live_host.py
Success: no issues found in 11 source files
exit: 0
```

Input/output highlights:

- `UserPromptSubmit` with synthetic prompt `Save` normalizes to `USER_INPUT`, reference `turn-1`, action `None`; prompt text is absent from the normalized event.
- Exact G0 environment reports read/search true and decision/write/atomic/auto-activation false.
- Version, OS, or architecture mismatch reports every capability false.
