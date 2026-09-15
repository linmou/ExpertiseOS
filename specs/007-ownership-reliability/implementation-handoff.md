# C007 Ownership and Reliability Implementation Handoff

**Intent**: Record the component implementation, reproducible local evidence, and exact integration work that remains.

## Provenance

- Branch: `007-ownership-reliability`
- Promoted C002-C004 base: `a121bf560a20937fa8d0e7017a13bd402427bb33`
- C004 producer commit included in that promotion: `633961d62a63ff761b992df768b1c04b173e2cd4`
- Planning commit: `71db13c`
- Verification date: 2026-09-14

## Delivered Boundary

- `ownership.py`: actual-user selection authority, sealed export/restore bindings, portable approved-state snapshots, atomic export, full bundle validation, collision preflight, identical-record no-op, ordered restore, retire/delete planning, explicit external limits, and uninstall data choice.
- `reliability.py`: canonical commit classification, Saved rendering gate, content-free recovery, receipt reconciliation, index repair, and explicit bounded degraded search health.
- `security.py`: restricted local transport validation, untrusted result handling support, deterministic secret minimization, controlled-location enumeration, and marker-free persistence audit reports.
- `benchmark_mvp.py`: deterministic 10,000-object lifecycle, retrieval, and approved-write benchmark with raw samples and environment metadata.

## Verification

| Gate | Result | Evidence |
|---|---:|---|
| Focused C007 suite | 31 passed | `artifacts/verification/c007-*.json` |
| Full repository suite | 218 passed, 3 skipped | `artifacts/verification/c007-suite.json` |
| Strict mypy | 18 files, 0 issues | `artifacts/verification/c007-mypy.json` |
| Ruff format/check | 18 files format-clean, 0 issues | local command output |
| Lifecycle bookkeeping | p95 0.001754 ms, pass | `artifacts/benchmarks/c007.json` |
| Warm local retrieval | p95 7.198481 ms, pass | `artifacts/benchmarks/c007.json` |
| Approved-write acknowledgement | p95 53.296186 ms, pass | `artifacts/benchmarks/c007.json` |

The export test consumes records from the actual promoted `BasicMemoryBackend` and `SQLiteState` public read methods in the same export. Network-denied, malicious-content, marker-audit, collision, retry, outage, and index-repair paths are covered.

## Integration-Owned Work

The promoted APIs do not yet expose the bulk methods described by the reconciled handoff contract:

- C002: content-free operation-state persistence and concrete receipt reconciliation.
- C003: bulk approved restore, identity digest inspection, scoped delete orchestration, and controlled-location descriptors.
- C004: bulk learning restore, learning-scope deletion, and controlled-location descriptors.
- C008: actual host selection binding consumption, result rendering, and uninstall service/host actions.

C007 deliberately exposes narrow protocols for these operations. Integration must supply adapters and real producer-to-consumer handoff tests; it must not replace the boundary with synthetic fixtures. Tasks T013, T021, and T044 remain open for this reason.

## Documentation Review

- `docs/implementation-status.md` requires an integration-owner update after C007 promotion.
- `README.md`, `docs/privacy-boundary.md`, and `docs/compatibility.md` are absent at this promoted base; no component-owned edits were made.
- Shared release and orchestration documents remain integration-owned.
