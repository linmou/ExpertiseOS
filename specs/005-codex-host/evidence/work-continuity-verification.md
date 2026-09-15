# Codex Work Continuity Verification

**Intent**: Demonstrate conservative checkpoints, C004 control consumption, and failure containment.

Command: focused C005 pytest command recorded in `foundation-verification.md`.

Results:

- Nested/open atomic state rejects a checkpoint.
- Unbalanced atomic end makes checkpoint state unknown and closed.
- Static hook evidence never makes `comparison_ready` true because live ordering is unverified.
- `should_observe` consumes C004 `ControlResolution` and remains false for the read-only profile.
- `should_retrieve` requires C004 approved recall, evidence-backed search, and no C004 exclusion match.
- Source, path subtree, and session exclusions each prevent retrieval forwarding.
- Service exception input `ServiceUnavailableError` produces `{available: false, value: null, error_type: ServiceUnavailableError}` while the host result remains `{task: complete, artifact: unchanged}`.

Focused result: `37 passed`; exit `0`.
