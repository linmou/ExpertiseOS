# G0 Research Decisions

**Intent**: Separate fixed implementation defaults from external claims that must be proven during the feasibility gate.

## Support Is Evidence-Gated

**Decision**: Pin only host, backend, integration, and OS combinations exercised by reproducible G0 checks. A host is write-capable only after its actual-user-event and proposal-binding fixture passes.

**Rationale**: Exact external APIs can invalidate authorization semantics.

**Alternatives considered**: Assuming latest releases, private host internals, or model arguments as approval are unsafe or brittle.

## Unsupported Authorization Becomes Read-Only

**Decision**: If trustworthy actual-user input is unavailable independently of model/tool output, report write capability as blocked/read-only.

**Rationale**: Capability reporting can narrow support without weakening approval.

**Alternatives considered**: Prompt compliance and generic tool permission violate the authorization boundary.

## Conservative Safe Checkpoints

**Decision**: Prefer explicit atomic-operation boundaries. Otherwise use the narrowest supported post-operation checkpoint and document the limitation.

**Rationale**: Avoid interruptions without synthesizing a universal event stream.

**Alternatives considered**: Timing heuristics, transcript polling, and background observation are unsupported and outside scope.

## Two Narrow Protocols

**Decision**: Define `HostAdapter` and approved-data-only `KnowledgeBackend` protocols with standard-library typing and immutable value objects whose fields are all required at construction.

**Rationale**: Downstream work needs stable boundaries and fakes, not a plugin framework. Required fields prevent silently omitted production context.

**Alternatives considered**: Abstract hierarchies, event buses, extensive dependency injection, and repository layers add no MVP value.

## Approved-Data Backend Boundary

**Decision**: Backend mutation methods represent already-authorized operations and accept no approval boolean. `operation_id` is the sole idempotency identity and is supplied separately from approved semantic content to every semantic mutation.

**Rationale**: Authorization belongs to the guarded service and must not be forgeable at storage. Separating command identity prevents retry metadata from becoming part of approved knowledge content.

**Alternatives considered**: Per-backend approval logic and unrestricted vendor methods duplicate or bypass enforcement.

## Minimal Tooling

**Decision**: Use Python 3.12, pytest, Ruff, and mypy. Runtime contract/fake code uses the standard library; add only verified dependencies required by G0.

**Rationale**: This covers executable, formatting, lint, and type gates without production architecture.

**Alternatives considered**: Web frameworks, task runners, and additional test frameworks are unnecessary.

## Basic Memory and License

**Decision**: Exercise a selected released Basic Memory version through public interfaces and record AGPL-3.0 distribution obligations before claiming a releasable package.

**Rationale**: Process separation does not settle obligations, and private-table integration is unstable.

**Alternatives considered**: Forking/replacing Basic Memory or assuming subprocess use removes obligations contradicts the plan or lacks evidence.

## Evidence Still To Be Produced

Implementation tasks must replace these unknown claims with evidence:

- exact Codex version, registration, lifecycle/user events, session identity, and OS;
- exact Claude Code version, registration, lifecycle/user events, session identity, and OS;
- exact Basic Memory version, public operations, metadata/relations, local search, delete/rebuild, and offline limits;
- exact host integration dependency and local transport;
- exact AGPL-3.0 obligations and pilot/public-release status.

An unresolved item at G0 close is an explicit compatibility limit or blocker.
