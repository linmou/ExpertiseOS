# Claude Code G0 Fixtures

**Intent**: Pin the sanitized environment and capability facts consumed by C006 tests without representing unexecuted live checks as support.

**Updated**: 2026-09-14 for component implementation `0dbabb2a6dd4630a5f9ae01bb078b2c1e6b57137` against integration commit `649cb66533e78901a71a0a1c7fbd268cb9929fe2`.

- Integration promotion: `649cb66533e78901a71a0a1c7fbd268cb9929fe2`
- C004 promotion received: `633961d62a63ff761b992df768b1c04b173e2cd4`
- Claude Code: `2.1.241`, build `c87e2742fc9a`
- Environment: macOS `15.1.1` build `24B91`, `arm64`, default permission mode
- Source: `specs/001-feasibility-bootstrap/evidence/claude-code/host-feasibility.md`

The installed public plugin and hook interface passed static discovery. The authenticated live activation, configuration-preservation, atomic-ordering, service-failure, and six-step actual-user decision fixtures were not run. Therefore automatic activation, atomic-boundary observation, decision validation, and persistent writes remain unavailable. Deterministic fixtures cannot promote those capabilities.
