# Implementation Plan: Consent Core

**Branch**: `002-consent-core` | **Date**: 2026-09-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-consent-core/spec.md`

## Summary

Implement the MVP's consent boundary as host-neutral Python domain models, a process-local candidate/grant lifecycle, a deterministic approval digest and gate, a guarded `KnowledgeService`, and minimal SQLite approval receipts. Every semantic write is tied to one exact actual-user decision and expected object versions. C001's explicit mutation methods receive a canonical `operation_id`, making retries idempotent when the canonical write succeeds before receipt completion. Basic Memory mapping, learning behavior, production host adapters, and final service wiring remain outside this component.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Python standard library plus the model/validation choice and narrow `HostAdapter`/`KnowledgeBackend` contracts delivered by C001
**Storage**: Volatile Python memory for candidates and grants; SQLite `state.db` for minimal approval receipts
**Testing**: pytest with C001 fake host/backend; mypy and repository static checks
**Target Platform**: Local Codex and Claude Code environments through one local service process
**Project Type**: Installable Python package with host-neutral core services
**Performance Goals**: Consent bookkeeping stays within the MVP approved-write acknowledgement target; benchmark ownership remains C007
**Constraints**: No unapproved content on disk, no unrestricted host-facing backend mutation, fail closed for writes and open for ordinary host work, offline-capable, optimistic versions, no dataclass field defaults
**Scale/Scope**: One user, one local repository/service, concurrent host sessions, bounded active in-memory proposals; approved corpus scale is tested by C007

## Constitution Check

*GATE: Passed before research and rechecked after design.*

| Principle | Design Evidence | Result |
|---|---|---|
| Explicit Approval Before Persistence | Volatile proposal and grant stores; gate binds actual user event, exact digest, session, adapter, action, and expected versions before any semantic write. | PASS |
| Work Continues, Unsafe Writes Stop | Service returns typed conflict/failure/incomplete outcomes and never reports Saved before exact read-back and receipt completion. | PASS |
| Local, Minimal, Inspectable State | One receipt table; no candidate table, unused-grant table, extra service, queue, or generic transaction framework. | PASS |
| Permission, Knowledge, Evidence, and Mastery Stay Separate | Save creates no learner evidence or mastery change; C004 owns the separate learner-state projection and schema extension. | PASS |
| Contracts and Verification Drive Delivery | Public contracts and state invariants are documented; tasks include unit, fake-backend integration, adversarial, type, static, and quickstart verification. | PASS |

Post-design check: PASS. The data model contains no durable candidate payload path; contracts expose guarded mutations only; every planned test maps to FR/SC and AT-04 through AT-08, AT-12, AT-13, and AT-15.

## Project Structure

### Documentation (this feature)

```text
specs/002-consent-core/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── consent-api.md
│   └── state-schema.md
├── checklists/
│   └── requirements.md
├── implementation-handoff.md # implementation closeout output for integration owner
└── tasks.md
```

### Source Code (repository root)

```text
src/expertiseos/
├── approval/
│   └── gate.py
├── domain/
│   ├── candidate_store.py
│   ├── errors.py
│   └── models.py
├── knowledge/
│   ├── backend.py       # C001-owned contract; change only through reconciliation
│   └── service.py
└── state/
    └── sqlite.py

tests/
├── fakes.py             # C001-owned fakes; compatible extension only through reconciliation
├── integration/
│   └── test_consent_commit_flow.py
└── unit/
    ├── test_approval_gate.py
    ├── test_candidate_lifecycle.py
    ├── test_cross_session_approval.py
    ├── test_decline_no_persistence.py
    ├── test_domain_models.py
    ├── test_exact_write.py
    ├── test_provenance.py
    ├── test_relationship_approval.py
    ├── test_stale_approval.py
    └── test_version_conflict.py
```

**Structure Decision**: Use the approved single-package layout. `domain` owns data and volatile lifecycle rules, `approval` owns grants/digest/gate behavior, `knowledge/service.py` is the only guarded mutation coordinator, and `state/sqlite.py` owns receipt persistence. No new layer is justified.

## Design Decisions

### Candidate and grant ownership

`CandidateStore` and `DecisionGrantStore` are process-local mappings. They expose explicit transition and expiry methods but no serializer. Host adapters register normalized actual-user decisions through the grant store; the core never parses host transcript text as authorization.

### Canonical approval binding

One function builds a semantic approval document from typed fields and hashes canonical UTF-8 JSON. Object keys and set-like category/subject/version collections are ordered deterministically; content and displayed ordered fields remain exact. IDs used only for runtime correlation and all timestamps are excluded unless they are part of displayed semantic content.

### Commit and retry

`KnowledgeService.commit()` validates through the gate, calls the matching explicit backend mutation with a stable `operation_id`, reads back the exact resulting record with versioned `get`, confirms current versions through `get_current_versions`, writes one receipt keyed by `operation_id`, then consumes the grant and approves the candidate. Repeating the same `operation_id` must return the original backend result and receipt. A separate operation journal is deferred because it cannot improve recovery when SQLite itself is unavailable and backend `operation_id` replay already supplies the required bounded reconciliation.

Grouped categorization, split, merge, or conflict-resolution effects are an approved ordered list of the same explicit create, update, relationship, and retirement primitives. Each effect receives a deterministic child `operation_id` derived from the approved parent `operation_id` and its ordered effect identity. Retrying the parent reuses the same child values, so completed effects reconcile without a generic workflow engine.

### Version and conflict semantics

Proposals capture every affected object version. The service verifies them at commit through the backend contract. Stale versions return a typed conflict containing current version references sufficient for a new proposal; no automatic rebase or last-write-wins path exists.

### Shared-file coordination

- C001 owns `knowledge/backend.py` and `tests/fakes.py`; C002 consumes the explicit mutation methods with final `operation_id` parameters, versioned `get`, and `get_current_versions` described in [consent-api.md](contracts/consent-api.md), without editing those shared files or adding another backend mutation API. Missing fake/backend behavior is returned to C001 through integration reconciliation.
- C002 owns the initial `knowledge/service.py` and `state/sqlite.py` contracts.
- C003 may add retrieval-facing methods without bypassing guarded mutations.
- C004 must submit learner/control migration extensions to this owner after reconciliation; no learner/control table is created here.
- C007 owns later deletion/reliability extensions and persistent-store audits.

## Verification Strategy

1. Domain tests cover all validation rules, legal/illegal candidate transitions, restart loss, and session-only decline suppression.
2. Approval tests cover exact matching and every forged, stale, replayed, cross-proposal, cross-session, cross-adapter, and modified-content case.
3. Service tests prove exact create/read-back/receipt ordering, revision/version conflict, relationship approval, retirement, direct-save limits, provenance scope, backend failure, receipt failure, and idempotent reconciliation.
4. One integration-level test passes a real `CandidateStore` proposal and real grant through the gate and guarded service into the conforming fake backend and SQLite receipt store.
5. Run targeted pytest, full component pytest, mypy on modified modules, repository static checks, and the quickstart verification. Preserve command output as integration evidence at promotion time.

## Complexity Tracking

No constitution violations or exceptional complexity are required.
