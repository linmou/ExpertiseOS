# C003 Component Verification

**Intent**: Record reproducible local evidence for the backend-retrieval component before integration promotion.

**Date**: 2026-09-14  
**Branch**: `003-backend-retrieval`  
**Upstream receipt**: `fc69741251f07ff1d5ed7fceb5c7463a823d120b`  
**C002 promotion**: `6fb115340c43ca8f4ae5afcc8a5f4306996c1779`

## Environment

- macOS 15.1.1, arm64, 8 logical CPUs
- Python 3.12.10
- pytest 8.4.2, Ruff 0.12.12, mypy 1.17.1
- Basic Memory 0.23.2, local public CLI only

## Results

| Gate | Exact command | Result |
|---|---|---|
| Full repository | `.venv-arm64/bin/python -m pytest -ra` | 119 passed in 71.20s |
| Lint | `.venv-arm64/bin/python -m ruff check .` | passed |
| Format | `.venv-arm64/bin/python -m ruff format --check .` | 59 files formatted |
| Types | `.venv-arm64/bin/python -m mypy src tests` | passed, 59 source files |
| Benchmark | `EXPERTISEOS_BENCHMARK_EVIDENCE=specs/003-backend-retrieval/evidence/retrieval-benchmark.json .venv-arm64/bin/python -m pytest tests/performance/test_retrieval_benchmark.py -q` | passed; warm p95 5.361 ms |

The full suite includes an actual Basic Memory create, versioned read, relationship write, indexed search, rebuild, and multi-version delete through supported local CLI commands. The benchmark uses 10,000 deterministic canonical notes, one warm-up, and 30 measured searches through the production `BasicMemoryBackend`; full metadata is in [retrieval-benchmark.json](retrieval-benchmark.json).

## Capability Boundary

- Canonical content lives in Basic Memory notes; the sidecar contains locators, operation digests/results, and hashed keyword tokens only.
- Search is bounded to 1 through 20 results and applies scope, subject, category, lifecycle, and explicit exclusions before return.
- Indexed search paginates until the requested filtered result count or backend exhaustion. Index failure uses local hashed-keyword fallback and reports degradation separately from canonical health.
- Retrieval is read-only and labels every result `untrusted_data`. It creates no grant, learner evidence, control change, or remote request.
- Backend deletion covers Basic Memory canonical versions and local derived tokens. Cross-store cleanup remains C007-owned.
- Producer-to-consumer authorization-to-recall coverage and shared implementation-status documentation remain integration-owned tasks T040 and T041.
