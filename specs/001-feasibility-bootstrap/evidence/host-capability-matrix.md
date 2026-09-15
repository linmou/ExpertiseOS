# Host Capability Matrix

**Intent**: Classify host support only from recorded evidence and make every missing authorization boundary fail closed.

Environment: macOS `15.1.1` build `24B91`, `arm64`; captured `2026-09-14T18:57:38Z`.

| Capability | Codex CLI 0.146.1 | Claude Code 2.1.241 |
|---|---|---|
| Supported activation surface | Plugin `add`; hooks stable | Plugin `install`; session `--plugin-dir` |
| Reversible removal surface | Plugin `remove` | Plugin `uninstall` |
| Configuration-preserving live setup/removal | Not run | Not run |
| Actual user-input schema | `UserPromptSubmit.prompt` | `UserPromptSubmit.prompt` |
| Session identity schema | `session_id`; `turn_id` also present | `session_id`; CLI accepts `--session-id` |
| Lifecycle/checkpoint schema | Session, prompt, tool, stop, end hooks documented | Hook lifecycle documented |
| Atomic boundary | Tool lifecycle is a candidate boundary; live ordering not validated | Hook lifecycle is a candidate boundary; live ordering not validated |
| Six-step live decision binding | Not run | Not run |
| Live service-failure continuity | Not run | Not run |
| Write status | **Blocked/read-only** | **Blocked/read-only** |

Static/public-interface feasibility is supported for both hosts. Neither host is write-capable because exact live proposal binding, one-use consumption, checkpoint ordering, and configuration-preserving install/uninstall have not passed. Deterministic tests validate the adapter contract only; they do not promote a host capability.

Evidence: [Codex](codex/host-feasibility.md), [Claude Code](claude-code/host-feasibility.md), `tests/integration/test_host_feasibility.py`, `tests/integration/test_no_write_without_user_event.py`, and `tests/integration/test_service_failure_continuity.py`.
