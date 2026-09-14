# expertiseOS Constitution

**Intent**: Keep implementation decisions aligned with the MVP's consent, local-first, learning, and simplicity requirements.

## Core Principles

### I. Explicit Approval Before Persistence

Unapproved candidate content MUST remain in process memory only. Every substantive knowledge, relationship, learner-evidence, mastery, or control-state mutation MUST be bound to an actual user event, the exact displayed content, the originating adapter and session, and relevant expected versions. Model claims, tool output, generic tool permission, stale grants, and cross-session events MUST NOT authorize writes.

### II. Work Continues, Unsafe Writes Stop

The host agent owns the user's task. expertiseOS MUST NOT become a task orchestrator or prevent ordinary host work when its service, storage, retrieval, or approval validation fails. A failed or unverifiable knowledge mutation MUST fail closed and MUST NOT report a false success.

### III. Local, Minimal, and Inspectable State

Approved knowledge, provenance, relationships, and versions belong behind the Basic Memory adapter. Minimal approvals, learner evidence, controls, and approved-object references may live in SQLite. Candidates and unused grants MUST remain volatile. The implementation MUST NOT add cloud sync, another generative model, an autonomous background worker, a general policy/workflow engine, or speculative infrastructure.

### IV. Permission, Knowledge, Evidence, and Mastery Stay Separate

Saving knowledge MUST NOT imply correctness or mastery. Learner-state changes MUST use approved evidence of the user's contribution, scoped to the relevant object version and context. Assistant-only output, retrieval frequency, task success with unknown contribution, and self-report MUST NOT silently advance demonstrated mastery.

### V. Contracts and Verification Drive Delivery

Components MUST preserve host-neutral domain contracts and keep host-specific parsing inside adapters. Each task set MUST trace to an MVP requirement or acceptance test. Implementation proceeds through explicit tasks and proportionate unit, integration, end-to-end, static, and smoke verification. Consent, privacy, and state-integrity failures are release blockers and cannot be offset by qualitative model behavior.

## Product Constraints

- Target Python 3.12 and one installable `expertiseos` package with one local service process.
- Support local Codex and Claude Code through one shared behavioral skill and thin adapters.
- Use optimistic version checks and content-bound, one-use decision grants.
- Keep pause, fatigue rest, target satisfaction, and full disable as distinct states.
- Keep retrieved knowledge as untrusted data with bounded provenance-aware recall.
- Preserve explicit export, restore, retire, delete, and uninstall data-choice behavior.
- Resolve unsupported host capabilities through accurate capability reporting; never weaken approval semantics.

## Development Workflow

1. Complete Spec Kit `specify`, `clarify`, `plan`, `tasks`, and read-only `analyze` before implementation.
2. Resolve every CRITICAL or HIGH analysis finding before implementation.
3. Implement dependency-ready tasks only, keeping shared-file ownership explicit.
4. Add focused tests for required behavior and negative paths in the same component change.
5. Run component checks locally, then real producer-to-consumer integration, end-to-end, and smoke checks after serial integration.
6. Record exact commands, results, commits, compatibility limits, and unresolved feasibility blockers.

## Governance

This constitution governs all component specifications, plans, tasks, implementation, and integration reviews. Changes require an explicit rationale tied to the MVP PRD or a verified feasibility constraint, an updated version, and review of affected Spec Kit artifacts. Simplicity is the default: new layers or dependencies require a concrete requirement or failing acceptance test.

**Version**: 1.0.0 | **Ratified**: 2026-09-14 | **Last Amended**: 2026-09-14
