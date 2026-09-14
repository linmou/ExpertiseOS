# Quickstart: Validate Product Integration

**Intent**: Provide the shortest repeatable path for implementing and checking C008 after its upstream promotion gate opens.

## Preconditions

1. Work on branch `008-product-integration` in its dedicated worktree.
2. Record the green integration promotion SHA containing reconciled C002-C007 contracts.
3. Confirm pinned Python, dependency, Codex, Claude Code, and OS versions from C001.
4. Confirm C004 exposes the finalized pass-only mastery advancement behavior.

## Implementation Order

1. Add contract tests for the public tool registry and forbidden backend surface.
2. Implement the thin composition facade and MCP registrations.
3. Add the single shared behavioral skill and its structural/behavior fixtures.
4. Add Scenario A-D fixtures and executable scenario tests.
5. Add grouped AT-01 through AT-16 coverage, then adversarial and offline runs.

## Verification

Run the repository-provided targeted command for `tests/e2e`, then the full test, static, and type-check commands defined by the promoted project configuration. Run live-host cases only against the pinned supported versions and record exact environment metadata.

For each run, retain command, exit code, tested SHA, promotion SHA, fixture versions, environment, actual edge artifacts, and safe output path. A failing upstream semantic assertion returns to its component owner; do not patch the shared skill to conceal it.

## Expected Product Checks

- No public backend write tool exists.
- Mutation without an exact fresh decision is rejected without persistence or false success.
- Both hosts use the same behavior source and shared durable state.
- Scenario A-D produce the exact expected visible and persistent outcomes.
- AT-01 through AT-16 have complete evidence.
- Adversarial content changes no grant, write, control, mastery, disclosure scope, or permission.
- Offline expertiseOS runtime retains local storage/state/search behavior with documented fallback.
