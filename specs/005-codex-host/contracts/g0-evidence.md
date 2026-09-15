# Contract: Required G0 Codex Evidence

Implementation may claim a capability only when the integration owner supplies immutable evidence with:

| Field | Required content |
|---|---|
| Host identity | Exact Codex product/surface and released version or commit |
| Environment | Operating system and permission mode |
| Mechanism | Supported installation/registration and lifecycle interface |
| Session proof | Stable session identity or proven lifecycle-bound generated identity |
| Actual-user proof | Event source and fixture distinguishing user input from assistant/tool/model content |
| Checkpoint proof | Supported atomic/conversational boundaries and conservative limitations |
| Activation proof | Fresh-session activation after consented onboarding and reversible removal |
| Failure proof | Ordinary Codex task completes when expertiseOS is unavailable |
| Fixture provenance | Exact command or manual procedure, input, expected output, actual output, exit/result, timestamp, and artifact hash/path |

## Gate Rules

- Documentation statements without a reproduced fixture are insufficient.
- Private/unsupported APIs are insufficient.
- A bypass found on any claimed event path must be recorded and reflected in capabilities.
- `can_validate_user_decisions=true` requires a passing adversarial fixture covering model arguments, assistant text, tool output, quoted Save, stale proposal, wrong session, and changed digest.
- `can_write=true` requires actual-user validation plus compatible C002 approval behavior.
- Missing evidence disables the affected capability; it does not permit an alternative semantic fallback.
