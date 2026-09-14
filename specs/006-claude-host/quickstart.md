# Quickstart Verification: Claude Code Host Adapter

**Intent**: Give implementers a short, reproducible path from upstream promotion through component and live-host evidence.

## Prerequisites

- Use the immutable integration promotion SHA containing approved C001-C004 contracts.
- Confirm C001 records a pinned Claude Code version, OS, permission mode, supported registration path, event mapping, and actual-user fixture result.
- If actual-user capture evidence is not passed, verify read-only capability behavior and stop the write-capable acceptance path as blocked.

## Component Verification

Run from the repository root after implementation:

```bash
pytest tests/contract/test_claude_code_adapter.py -q
pytest tests/integration/test_claude_code_service.py -q
mypy src/expertiseos/hosts/claude_code.py tests/contract/test_claude_code_adapter.py tests/integration/test_claude_code_service.py
ruff check src/expertiseos/hosts/claude_code.py tests/contract/test_claude_code_adapter.py tests/integration/test_claude_code_service.py tests/e2e/test_claude_code_live.py
```

Required negative cases include non-user origins, quotes, generic permission, ambiguity, stale and changed bindings, cross-session/host events, nested atomic operations, exclusions, session expiry, timeout, and malformed service response.

## Producer-to-Consumer Checks

Run the integration test with actual upstream objects and services, not synthetic boundary replacements:

1. Feed C001's sanitized Claude actual-user event and active binding into the adapter.
2. Pass the adapter observation to C002 and verify the exact approved mutation commits once.
3. Retrieve that same committed object through C003 and verify Claude receives its actual ID/version and untrusted health-labeled result.
4. Apply C004 pause/disable/exclusion outputs and verify source forwarding and recall permissions match upstream resolution.
5. End the session and verify C002 expiry plus empty adapter volatile state.

## Pinned Live-Host Check

Run only on the C001-supported environment:

```bash
pytest tests/e2e/test_claude_code_live.py -q --run-live-claude
```

Record host version, OS, permission mode, fixture version, command, exit status, event names observed, sanitized input-output pairs, capability result, and limitation. The live check must demonstrate activation, atomic/checkpoint behavior, an actual-user Save committing exactly once, model-only rejection, session expiry, and host-task continuation during service failure.

## Completion Gate

The component is ready for serial integration only when contract, integration, mypy, Ruff, and supported live-host checks pass, or when the exact unsupported capability is recorded and `can_write=false`. A read-only result does not satisfy the MVP's write-capable Claude acceptance requirement.
