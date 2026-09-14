# G0 Verification Quickstart

**Intent**: Give implementers the shortest reproducible path through the feasibility gate.

## Preconditions

- Python 3.12.
- Pinned candidate host/backend versions.
- Disposable host configuration and approved-only backend fixtures.
- Outbound blocking available for the local-only check.

## Order

1. Create an isolated environment and install development dependencies.
2. Run format, lint, strict type, import, unit, and integration checks defined by `pyproject.toml`.
3. For each host, verify activation, config preservation, uninstall, and the six-step actual-user-decision fixture on the pinned version.
4. For Basic Memory, run approved create/read/search/metadata/relation/delete/rebuild/health round trips through public interfaces.
5. Block outbound access after setup and rerun supported backend scenarios, including keyword fallback where needed.
6. Review the exact Basic Memory distribution arrangement for AGPL-3.0 obligations.
7. Record command/manual steps, environment, fixture, result, and limitation. Missing authorization evidence means read-only/blocked.

## Required Stable Commands

```text
format check
lint
mypy
package import smoke
unit tests
integration tests
offline backend fixture
live/manual host evidence fixture
```

## Stop Conditions

- No write support claim without actual-user-input evidence.
- No local backend claim when runtime needs a remote memory/model service.
- No downstream promotion with undocumented compatibility/license blockers.
- No weakening approval or local-first semantics to pass a check.
