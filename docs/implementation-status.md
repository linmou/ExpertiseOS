# expertiseOS MVP Implementation Status

**Intent**: State what is integrated and verified without implying unfinished MVP capabilities are available.

**Updated**: 2026-09-14  
**Integration branch**: `integration/expertiseos-mvp`
**Verified through**: C008 tested code `c642f3dc214ef56059e6e87418e6f3732b7e3e4e`

## Integrated Components

- C001 feasibility/bootstrap is promoted at `f7b1eb59a7d1837c367095e195ea7a42ead20098`.
- C002 consent core is promoted at `6fb115340c43ca8f4ae5afcc8a5f4306996c1779`; delegated authorization and Decimal canonicalization corrections through `70d182d` are supplied to C008.
- C003 backend retrieval is promoted at `166f196638e66e4aea324ee12d117507963e7629`.
- C004 learner evidence and controls are promoted at `633961d62a63ff761b992df768b1c04b173e2cd4`.
- C005 Codex host is promoted at `edf03b653ee59f9c8a2db2f7c1df7b591e5a05d4`.
- C006 Claude host is promoted at `59899b8ee88f04a8691d1ff61fd2ae9a9bf2a779`.
- C007 ownership/reliability is promoted at `2e9555772b6dfefd9aab8403910f4280ca3de44a`.
- C008 product integration passed its complete integration gate at `c642f3dc214ef56059e6e87418e6f3732b7e3e4e`.

## C003 Verified Behavior

- Approved mutations cross C002's grant and commit gate before Basic Memory persistence.
- Canonical versions, provenance, relationships, lifecycle changes, and operation replay round-trip through Basic Memory `0.23.2` public local CLI commands.
- Recall is bounded to 20, filters approved active records, marks recalled text as untrusted data, and persists no query content.
- Indexed retrieval degrades visibly to a local hashed-keyword fallback; canonical and index health remain distinct.
- Backend-scope retire, delete, and rebuild remove obsolete active retrieval/index traces.
- Independent component verification passed 119 tests, strict mypy, Ruff, real CLI/offline cases, and a 10,000-note warm retrieval p95 of `5.200 ms`.

## C004 Verified Behavior

- Only approved `pass` evidence contributes to mastery; other outcomes remain inspectable with zero contribution.
- Positive nondecreasing integer thresholds are configurable, with explicit defaults `1, 1, 1, 1, 2`.
- Numeric thresholds cannot bypass autonomous requirements for independent passes, distinct tasks and sessions, transfer, contradiction clearance, and explicit agreement.
- Controls resolve disable, pause, fatigue rest, target satisfaction, and active learning in fixed precedence with separate recall permission.
- SQLite persistence covers evidence, versioned controls, global idempotent progress, literal exclusions, and approved-reference-only deferred activities.

## C005 Verified Behavior

- The pinned Codex profile exposes approved read and bounded search, normalizes documented hook shapes, and consumes C004 controls and exclusions without duplicating their policy.
- Active, paused, fatigue-rest, target-satisfied, disabled, source-excluded, path-excluded, and session-excluded paths pass the C004-to-C005 handoff.
- Session cleanup and optional-service failure containment preserve ordinary host work.
- Static plugin add/remove commands are reversible, but configuration preservation is not claimed without live evidence.
- Automatic activation, actual-user decision validation, persistent writes, and live atomic-boundary delivery remain unavailable and are reported as such.

## C006 Verified Behavior

- The pinned Claude profile exposes approved read and bounded search, normalizes lifecycle events, and consumes C004 controls and exclusions directly.
- Exact Save, Skip, Edit, and direct-save forms are parsed, while ambiguous and forged/model-only forms cannot authorize a write.
- Session expiry, bounded C003 retrieval, malformed-response handling, and service-failure containment preserve ordinary host work.
- Only a typed C002 committed result maps to Saved.
- Automatic activation, configuration preservation, actual-user decision validation, persistent writes, and live atomic-boundary delivery remain unavailable and are reported as such.

## C007 Verified Behavior

- Actual approved Basic Memory knowledge and SQLite learning/control state export together in a portable validated bundle.
- Restore preserves canonical IDs, versions, provenance, pass evidence, numeric thresholds, progress events, exclusions, and deferred references; divergent replay or collisions fail explicitly.
- Approved deletion removes canonical records plus dependent evidence and deferred activities and remains idempotent.
- Canonical failure never renders Saved; index degradation remains separate from commit status and uses bounded local fallback.
- Persistence audits, explicit uninstall data choices, local transport restrictions, and the deterministic 10,000-object benchmark pass.

## C008 Verified Behavior

- One stateless facade and explicit MCP allowlist expose bounded reads, proposals, guarded commits, learning/control inspection, ownership operations, capabilities, and health without backend writers or approval booleans.
- Learning evidence, control changes, deferred removal, and deletion use exact C002 proposal/grant binding, actual C004/C007 writers, readback, and one canonical `operation_id`; only completed effects render Saved.
- Codex and Claude use the same host-neutral behavior skill while retaining their proven capability limits.
- Scenario A-D and deterministic AT-01 through AT-16 pass, including cross-host state, adversarial content, offline fallback, ownership, and pass-only adjustable mastery checks.
- Integration verification passed 97 integration tests, 62 end-to-end tests, 397 full-suite tests, strict mypy, Ruff, offline checks, health smoke, and all 10,000-object benchmark thresholds.

## Current Limits

- Codex and Claude persistent writes remain unavailable until authenticated six-step host decision fixtures pass.
- Public distribution remains blocked pending Basic Memory AGPL packaging review.
