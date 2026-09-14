# Codex Host Feasibility

**Intent**: Record exactly what the pinned Codex installation and public hook contract prove, and keep unexecuted write authorization disabled.

- Evidence ID: `codex-host-20260914`
- Component: Codex CLI `0.146.1`
- Environment: macOS `15.1.1` build `24B91`, `arm64`
- Captured: `2026-09-14T18:57:38Z`

## Installed Interface

Commands, each exit status `0`:

```text
codex --version
codex features list
codex plugin --help
```

Observed: `codex-cli 0.146.1`; `hooks stable true`; plugin commands include `add` and `remove`. The public hook documentation at <https://learn.chatgpt.com/docs/hooks> describes `SessionStart`, `UserPromptSubmit`, tool lifecycle, `Stop`, and `SessionEnd`. `UserPromptSubmit` includes `session_id`, `turn_id`, and the submitted `prompt`. Project and plugin hooks remain subject to workspace trust review.

Result: `pass` for installed hook/plugin interface discovery and static event-schema feasibility.

## Six-Step Decision Fixture

Fixture: `tests/integration/test_host_feasibility.py`, using adversarial inputs from `tests/fixtures/host_events.json`.

The deterministic adapter fixture proves the required policy sequence: activate a proposal, reject model-originated approval, wait for a safe checkpoint, bind one matching actual-user event, consume the grant once, and fail closed without interrupting ordinary work. The live authenticated Codex host was not modified and this six-step sequence was not executed through a real Codex session.

Result: `not_run` for live decision binding, lifecycle/checkpoint delivery, and failure-continuity delivery. Exit status: not applicable.

## Setup Reversibility

The installed CLI exposes supported plugin `add` and `remove` commands. No expertiseOS plugin was installed, so configuration preservation and uninstall were not executed against user configuration.

Result: `not_run` for live activation, configuration preservation, and uninstall. Exit status: not applicable.

## Capability Effect

Session and actual-prompt fields are statically available, but no live record proves exact proposal binding or one-use authorization. Codex support is therefore read-only; persistent writes are blocked pending the live six-step fixture. No model, tool, quoted, stale, cross-session, or cross-host text may substitute for `UserPromptSubmit` evidence.
