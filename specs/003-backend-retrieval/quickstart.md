# Quickstart: Backend Retrieval Verification

**Intent**: Provide a minimal reproducible verification path after upstream contracts are promoted.

## Preconditions

- C001's green integration SHA is merged with its pinned Basic Memory version and backend contract.
- C002's green integration SHA is merged with guarded mutations, domain models, and canonical `operation_id` replay semantics.
- Basic Memory completed documented local setup; no remote memory or embedding credentials are configured.

## Focused Verification

```bash
pytest tests/contract/test_knowledge_backend_contract.py
pytest tests/integration/test_basic_memory_adapter.py tests/integration/test_provenance.py tests/integration/test_relationships.py
pytest tests/integration/test_recall.py tests/integration/test_keyword_fallback.py
pytest tests/integration/test_retire_delete_backend.py tests/integration/test_index_failure_rebuild.py
```

Expected evidence includes exact approved round trips, stale-version rejection, ordinary recall exclusions, bounds at 20 or lower, visible local fallback, and deletion/rebuild removal of obsolete active index traces.

## Producer-to-Consumer Integration

```bash
pytest tests/integration/test_authorized_write_to_recall.py
```

The integration-owned test must authorize through C002, persist through the real adapter, and consume the same artifact through retrieval without replacing either side with a synthetic object.

## Local-Only Smoke Check

```bash
pytest tests/integration/test_keyword_fallback.py -k network_disabled
```

Record Basic Memory version, OS, index mode, and whether a local model download occurred during setup. Host provider inference is outside this assertion.

## Performance Evidence

```bash
pytest tests/performance/test_retrieval_benchmark.py --benchmark-corpus-size=10000
```

Record hardware, OS, Python and Basic Memory versions, index configuration, corpus size, warm-up, samples, and p95. Correctness remains release-blocking even if latency passes.
