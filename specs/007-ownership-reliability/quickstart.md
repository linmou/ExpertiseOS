# Verification Quickstart: Ownership and Reliability

**Intent**: Give implementers one concise path from focused checks to C008 integration evidence.

## Preconditions

- C002-C004 producer contracts are integrated at a recorded promotion SHA.
- Python 3.12 uses the C001-pinned Basic Memory version.
- Tests use isolated product roots and do not inspect host-owned transcripts.

## Verification Sequence

```bash
pytest tests/unit/test_ownership_models.py tests/unit/test_reliability.py tests/unit/test_security_boundary.py
pytest tests/integration/test_export_restore.py tests/integration/test_retire_delete.py tests/integration/test_uninstall_data_choice.py
pytest tests/integration/test_backend_outage.py tests/integration/test_index_failure_rebuild.py tests/integration/test_idempotent_retry.py tests/integration/test_startup_recovery.py
pytest tests/integration/test_injection_boundary.py tests/integration/test_no_candidate_persistence_audit.py tests/integration/test_keyword_fallback.py tests/integration/test_no_network_runtime.py
mypy src/expertiseos/ownership.py src/expertiseos/reliability.py src/expertiseos/security.py benchmarks/benchmark_mvp.py
python benchmarks/benchmark_mvp.py --corpus-size 10000 --output artifacts/benchmarks/c007.json
```

## Required Evidence

- Export and restore reports show exact counts, stable IDs, digests, collisions, and index status.
- Delete reports enumerate product-controlled targets and external limits.
- Failure logs record injected boundary, operation ID, status, and object/receipt counts without candidate content.
- Audit reports enumerate persistent locations and prove the runtime marker absent after negative fixtures.
- Network-denied evidence records zero external expertiseOS calls while local scenarios pass.
- Benchmark JSON records command, commit, corpus, versions, hardware, samples, and p95 verdicts.

## Integration Gate

C008 passes actual C002-C004 output into C007 and actual C007 results into AT-13 through AT-16. Synthetic replacement at either edge is not integration evidence.
