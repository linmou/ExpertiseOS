# Outbound-Denied Backend Evidence

**Intent**: Verify that the supported local read and bounded keyword-search path does not require outbound network access after setup.

- Evidence ID: `basic-memory-offline-20260914`
- Component: Basic Memory `0.23.2`
- Runtime: Python `3.12.10`, `arm64`
- Environment: macOS `15.1.1` build `24B91`
- Fixture: `tests/fixtures/approved_knowledge.json`
- Captured: `2026-09-14T18:57:38Z`

Command:

```text
.venv-arm64/bin/python -m pytest -q tests/integration/test_local_backend_offline.py
```

Observed result: `1 passed`; exit status `0`.

After isolated local setup and an approved note write, the test invokes Basic Memory read and search through macOS `sandbox-exec` with `(deny network*)`. Exact content read and bounded keyword search both succeed. Semantic search is explicitly disabled; keyword mode is the verified offline fallback. No remote expertiseOS memory service or second generative-model API key is used.

Result: `pass` for the supported post-setup read and keyword-search path. The outbound-denial fixture is macOS-specific, and offline semantic indexing is not claimed.
