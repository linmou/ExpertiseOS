# Codex G0 Event Fixtures

**Intent**: Preserve the minimal public hook shapes used by C005 contract tests without claiming live authenticated delivery.

- Codex CLI: `0.146.1`
- OS: macOS `15.1.1` build `24B91`, `arm64`
- Evidence: `specs/001-feasibility-bootstrap/evidence/codex/host-feasibility.md`
- Status: static schema only; live activation, checkpoint ordering, actual-user binding, configuration preservation, and failure continuity were not run

`g0_events.json` contains synthetic values matching the documented public fields. The prompt is test data and is discarded during normalization. These fixtures cannot enable write capability.
