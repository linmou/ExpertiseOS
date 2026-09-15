# Codex User Decision Verification

**Intent**: Record that static Codex user-prompt schemas cannot authorize persistent writes.

Test input/output pairs:

| Input | Output |
|---|---|
| Checkpoint/model/tool-shaped event | `NOT_USER_INPUT`; zero grants/writes |
| User event with no action | `AMBIGUOUS_ACTION`; zero grants/writes |
| User event from Claude adapter | `WRONG_ADAPTER`; zero grants/writes |
| User event from another session | `WRONG_SESSION`; zero grants/writes |
| Save/Edit/Skip on static Codex schema | `MISSING_USER_PROVENANCE`; zero grants/writes |
| Unsupported confirm-change action | `ACTION_NOT_ALLOWED`; zero grants/writes |
| Second simultaneous proposal | rejected for external disambiguation |

```text
.venv/bin/python -m pytest -q tests/unit/test_candidate_lifecycle.py tests/unit/test_cross_session_approval.py tests/integration/test_no_write_without_user_event.py tests/e2e/test_acceptance_consent.py
................... [100%]
19 passed in 0.12s
exit: 0
```

The authenticated six-step live Codex fixture remains not run. This record is negative-boundary evidence only and does not enable `can_validate_user_decisions` or `can_write`.
