# Implementation Plan: Ownership and Reliability

**Intent**: Turn C007 ownership and failure requirements into a small implementation with explicit upstream contracts and reproducible integrity evidence.

**Branch**: `007-ownership-reliability` | **Date**: 2026-09-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-ownership-reliability/spec.md`

## Summary

Add portable export/restore, retire/delete support, explicit uninstall data choice, bounded recovery and index repair, keyword degradation, untrusted-data guards, a persistent-location audit, and deterministic performance evidence. C007 consumes narrow approved-state/backend/learner-state interfaces from C002-C004 and exposes direct helpers to C008; it does not own shared service wiring or host adapters.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Python standard library plus the C001-pinned Basic Memory adapter behind C003's `KnowledgeBackend` contract
**Storage**: Basic Memory for canonical approved knowledge/indexes; SQLite `state.db` for receipts, learner/control state, and content-free recovery markers; JSON/JSONL and Markdown exports
**Testing**: pytest unit/integration tests, mypy for modified Python, deterministic benchmark CLI, network-disabled integration fixture
**Target Platform**: Local user-owned macOS/Linux environments supported by pinned Codex and Claude Code integrations
**Project Type**: Single installable local Python package and one local service process
**Performance Goals**: bookkeeping p95 <200 ms; warm retrieval p95 <1 s over 10,000 objects; approved-write acknowledgment p95 <1 s excluding indexing and host-model latency
**Constraints**: no unapproved persistence; ordinary work continues while unsafe writes stop; no public listener by default; no external memory/embedding call after setup; no semantic recovery or silent collision merge
**Scale/Scope**: one local user's repository, deterministic 10,000-object corpus, bounded retrieval and bounded content-free repair records

## Constitution Check

*GATE: Passed before Phase 0 and re-checked after Phase 1 design.*

| Principle | Design evidence | Result |
|---|---|---|
| Explicit Approval Before Persistence | Trusted actual-user export/restore selection events bind exact requests without redundant confirmation; retire/delete use upstream exact approval; operation markers contain no semantic content. | PASS |
| Work Continues, Unsafe Writes Stop | Canonical failures return non-success; index failures preserve completed canonical writes and surface degradation. | PASS |
| Local, Minimal, Inspectable State | Three direct modules, one documented bundle, and existing backend/SQLite stores; no service, queue, or framework is added. | PASS |
| Knowledge, Evidence, Permission, Mastery Separate | Export keeps record classes distinct; rebuild and retry cannot create evidence, mastery, progress, or approval. | PASS |
| Contracts and Verification Drive Delivery | Every FR/SC maps to tests or benchmark evidence; upstream extensions and downstream handoffs are explicit. | PASS |

Post-design check: only approved records or content-free operation metadata persist; contracts expose no unrestricted host write path; acceptance-critical negative paths have tasks. No exception is needed.

## Project Structure

### Documentation (this feature)

```text
specs/007-ownership-reliability/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── export-manifest.schema.json
│   ├── integration-handoffs.md
│   └── ownership-api.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/expertiseos/
├── ownership.py
├── reliability.py
└── security.py

tests/
├── unit/test_ownership_models.py
├── unit/test_reliability.py
├── unit/test_security_boundary.py
└── integration/
    ├── test_export_restore.py
    ├── test_retire_delete.py
    ├── test_uninstall_data_choice.py
    ├── test_backend_outage.py
    ├── test_index_failure_rebuild.py
    ├── test_idempotent_retry.py
    ├── test_startup_recovery.py
    ├── test_injection_boundary.py
    ├── test_no_candidate_persistence_audit.py
    ├── test_keyword_fallback.py
    └── test_no_network_runtime.py

benchmarks/benchmark_mvp.py
```

**Structure Decision**: Three package modules consume direct protocols from upstream owners. No repository layer, worker, migration framework, or second service is added. All new Python files begin with the requested shebang and one-line purpose comment.

## Component Boundaries

### C007-owned behavior

- Serialize approved snapshots into a portable bundle and validate/restore them.
- Plan and execute exact retire/delete scopes through guarded upstream operations.
- Return an explicit uninstall keep/delete plan for C008/host installers.
- Reconcile approved operations and index repairs by `operation_id`, the sole idempotency identity, after failure/restart.
- Expose degraded search health and invoke C003's bounded keyword fallback.
- Envelope retrieved material as untrusted data and minimize sensitive excerpts.
- Audit configured expertiseOS-controlled persistent locations for a candidate marker.
- Generate benchmark evidence with corpus and environment metadata.

### Upstream extension requests

- **C002/integration** owns concrete additions to `src/expertiseos/state/sqlite.py` and `src/expertiseos/knowledge/service.py`: content-free operation status, receipt enumeration, exact retire/delete entry points, and reconciliation.
- **C003** owns backend/index additions: deterministic approved snapshots, restore/delete primitives, index health/rebuild, keyword search, and canonical digest lookup.
- **C004** owns learner/control semantics and schema contracts; C007 requests approved snapshot enumeration, restore, excerpt deletion, and dependent deferred cleanup from C004, while C002/integration owns concrete SQLite migrations.
- C007 supplies contract tests and protocol shapes; it does not edit those shared files.

### Downstream handoff to C008

- Call these operations only after capability and approval checks.
- Wire host/service uninstall actions outside C007.
- Produce trusted request bindings from actual export/restore selection events and preserve `committed`, `degraded`, `conflict`, and `repair_required` statuses; Saved is UI text derived only from `committed`.
- Run producer-to-consumer AT-13 through AT-16 coverage with actual artifacts.

## Delivery Phases

1. Freeze protocols, schema, statuses, and fixtures.
2. Implement reliability/idempotency/search-health helpers and unit tests.
3. Implement export validation/restore and round-trip tests.
4. Implement retire/delete/uninstall and persistent-location audit.
5. Implement untrusted-data/local checks and network-disabled degradation coverage.
6. Run benchmark, mypy, component suite, and integration handoff tests.

## Complexity Tracking

No constitution violations or complexity exceptions.
