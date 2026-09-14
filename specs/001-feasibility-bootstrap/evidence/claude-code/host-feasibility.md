# Claude Code Host Feasibility

**Intent**: Record exactly what the pinned Claude Code installation and public hook contract prove, and keep unexecuted write authorization disabled.

- Evidence ID: `claude-host-20260914`
- Component: Claude Code `2.1.241`, build commit `c87e2742fc9a`
- Environment: macOS `15.1.1` build `24B91`, `arm64`
- Captured: `2026-09-14T18:57:38Z`

## Installed Interface

Commands, each exit status `0`:

```text
claude --version
claude --help
claude plugin --help
```

Observed: `2.1.241 (Claude Code)`; the CLI exposes `--include-hook-events`, `--session-id`, and `--plugin-dir`; plugin commands include `install` and `uninstall`. The public hook documentation at <https://code.claude.com/docs/en/hooks> describes `UserPromptSubmit` with `session_id` and `prompt`.

Result: `pass` for installed hook/plugin interface discovery and static event-schema feasibility.

## Six-Step Decision Fixture

Fixture: `tests/integration/test_host_feasibility.py`, using adversarial inputs from `tests/fixtures/host_events.json`.

The deterministic adapter fixture proves the required policy sequence: activate a proposal, reject model-originated approval, wait for a safe checkpoint, bind one matching actual-user event, consume the grant once, and fail closed without interrupting ordinary work. The live authenticated Claude Code host was not modified and this six-step sequence was not executed through a real session.

Result: `not_run` for live decision binding, lifecycle/checkpoint delivery, and failure-continuity delivery. Exit status: not applicable.

## Setup Reversibility

The installed CLI exposes supported plugin `install` and `uninstall` commands and a session-scoped `--plugin-dir` activation path. No expertiseOS plugin was installed, so configuration preservation and uninstall were not executed against user configuration.

Result: `not_run` for live activation, configuration preservation, and uninstall. Exit status: not applicable.

## Capability Effect

Session and actual-prompt fields are statically available, but no live record proves exact proposal binding or one-use authorization. Claude Code support is therefore read-only; persistent writes are blocked pending the live six-step fixture. No model, tool, quoted, stale, cross-session, or cross-host text may substitute for `UserPromptSubmit` evidence.
