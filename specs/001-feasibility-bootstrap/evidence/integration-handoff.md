# Feasibility Bootstrap Integration Handoff

**Intent**: Give the integration owner the exact contracts, compatibility limits, checks, and evidence needed to promote C001 without editing integration-owned status documents.

## Delivered

- Installable Python 3.12 `expertiseos` package and non-networked bootstrap entrypoint.
- Host-neutral `HostAdapter` contract with lifecycle ordering, actual-user origin, session scope, safe-checkpoint, evidence, and exact decision-binding validation.
- `KnowledgeBackend` contract with approved content, stable identity, current/historical reads, bounded search, optimistic version checks, semantic mutation idempotency, rebuild, and separate health state.
- Deterministic fakes and 37 non-external tests for downstream development.
- Public Basic Memory and macOS outbound-denied probes; full suite result is 39 passed.

## Compatibility Status

Codex CLI `0.146.1` and Claude Code `2.1.241` expose plausible plugin, hook, actual-prompt, and session surfaces. Neither live authenticated six-step decision fixture was run, so both integrations remain read-only and writes are blocked. Do not promote either to write-capable from deterministic tests.

Basic Memory `0.23.2` passes public CLI create/current-read/metadata/relationship representation/bounded keyword search/reindex/delete and outbound-denied read/search. It lacks native public CLI coverage for exact history, expected-version mutations, batched current versions, expertiseOS `operation_id`, and split canonical/index health; a later production adapter/sidecar must supply and test those semantics.

The backend is AGPL-3.0-or-later. Private local evaluation may proceed; public/customer distribution remains blocked pending packaging-specific legal review.

## Integration Evidence

- Host classification: [host-capability-matrix.md](host-capability-matrix.md)
- Backend: [basic-memory/public-cli.md](basic-memory/public-cli.md)
- Offline: [offline/network-denied.md](offline/network-denied.md)
- License: [basic-memory-license.md](basic-memory-license.md)
- Verification: [bootstrap-verification.md](bootstrap-verification.md)
- Scope: [scope-audit.md](scope-audit.md)

Integration should consume the public contracts from `src/expertiseos/hosts/contract.py` and `src/expertiseos/knowledge/backend.py`; vendor internals are not part of the handoff.
