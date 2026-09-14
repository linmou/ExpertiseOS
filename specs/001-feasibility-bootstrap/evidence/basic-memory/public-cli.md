# Basic Memory Public CLI Evidence

**Intent**: Record the supported local Basic Memory behavior actually exercised and identify semantics that require an expertiseOS adapter.

- Evidence ID: `basic-memory-cli-20260914`
- Component: Basic Memory `0.23.2`
- Runtime: Python `3.12.10`, `arm64`
- Environment: macOS `15.1.1` build `24B91`
- Fixture: `tests/fixtures/approved_knowledge.json`
- Captured: `2026-09-14T18:57:38Z`

Command:

```text
.venv-arm64/bin/python -m pytest -q tests/integration/test_backend_feasibility.py
```

Observed result: `1 passed`; exit status `0`.

The test creates an isolated local `g0` project through public commands, writes two approved notes, reads exact content and frontmatter, preserves a wiki relationship in content, performs bounded keyword search with a returned `external_id`, rebuilds the search index, deletes by public command, and confirms the note is absent. It sets `BASIC_MEMORY_CONFIG_DIR` and `BASIC_MEMORY_HOME` to disposable paths and disables semantic search and auto-update.

## Compatibility Limits

The Basic Memory CLI does not expose the expertiseOS contract's exact historical-version retrieval, expected-version mutations, batched current-version lookup, semantic `operation_id` replay/conflict behavior, or separate canonical/index health result. Stable Basic Memory `external_id` values are available, but production identity and version mapping still require the planned narrow adapter/sidecar.

These missing native operations are not silently simulated in this external proof. `tests/unit/test_backend_contract.py` proves the required expertiseOS contract deterministically; it is not evidence that Basic Memory natively supplies those semantics.

Result: `limited`. Public create/current-read/metadata/relationship representation/bounded keyword search/reindex/delete passed. Production adapter mapping remains unimplemented and is outside this component.

Installation note: initial `uv sync` rejected Basic Memory's pinned prerelease `fastmcp==4.0.0b1`. Allowing prereleases then failed on the existing x86_64 Python because `onnxruntime==1.30.0` has no matching macOS x86_64 wheel. A separate ARM Python `3.12.10` environment installed successfully; no experiment behavior was changed.
