# Quickstart: Validate Product Integration

**Intent**: Provide the shortest repeatable path for implementing and checking C008 after its upstream promotion gate opens.

## Preconditions

1. Work on branch `008-product-integration` in its dedicated worktree.
2. Use starting receipt `d754a5a56596cce559688e4066042235bd3ea35e`, which contains immutable C001-C007 promotion `2e9555772b6dfefd9aab8403910f4280ca3de44a`.
3. Use Python 3.12 and the dependency environment verified by C001; Codex and Claude write/live capabilities remain false unless authenticated fixtures prove them.
4. Confirm C004 exposes the finalized pass-only mastery advancement behavior.

## Verified Commands

Run checks with C008 sources and the already verified integration environment:

```bash
rtk env PYTHONPATH=src /Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration/.venv-arm64/bin/python -m pytest ...
rtk env PYTHONPATH=src /Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration/.venv-arm64/bin/python -m ruff ...
rtk env PYTHONPATH=src /Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration/.venv-arm64/bin/python -m mypy ...
```

The system `mypy` launcher uses a pre-3.12 interpreter and cannot parse the project's Python 3.12 type-alias syntax. A local `uv run` also attempts dependency re-resolution and currently rejects Basic Memory's pinned FastMCP prerelease. Neither is an implementation failure or permission to change project configuration.

## Implementation Order

1. Add contract tests for the public tool registry and forbidden backend surface.
2. Implement the thin composition facade and MCP registrations.
3. Add the single shared behavioral skill and its structural/behavior fixtures.
4. Add Scenario A-D fixtures and executable scenario tests.
5. Add grouped AT-01 through AT-16 coverage, then adversarial and offline runs.

## Verification

Run the targeted command for `tests/e2e`, then the full test, static, and type-check commands above. Run live-host cases only against the pinned supported versions and record exact environment metadata.

For each run, retain command, exit code, tested SHA, fixture versions, environment, actual edge artifacts, and safe output path. The integration review maps the tested SHA to a promotion SHA only after its audit and smoke gates. A failing upstream semantic assertion returns to its component owner; do not patch the shared skill to conceal it.

## Expected Product Checks

- No public backend write tool exists.
- Mutation without an exact fresh decision is rejected without persistence or false success.
- Both hosts use the same behavior source and shared durable state.
- Scenario A-D produce the exact expected visible and persistent outcomes.
- AT-01 through AT-16 have complete evidence.
- Adversarial content changes no grant, write, control, mastery, disclosure scope, or permission.
- Offline expertiseOS runtime retains local storage/state/search behavior with documented fallback.
