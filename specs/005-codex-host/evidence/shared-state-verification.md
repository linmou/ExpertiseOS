# Codex Shared State Verification

**Intent**: Verify shared approved reads and volatile session cleanup without adding host-owned storage.

- `tests/integration/test_codex_shared_service.py` creates approved objects through the promoted backend/service bundle and reads the same ID/version through the optional Codex-side call boundary.
- Returned search data remains `UNTRUSTED_DATA` and explicitly degraded keyword mode.
- `tests/contract/test_codex_session_expiry.py` expires active C002 candidate and unused grant state, clears the adapter binding, accepts abrupt session cleanup, and rejects late/repeated events.
- Candidate marker content exists only in the in-memory test proposal. No C005 database, log, temporary file, retry queue, or recovery artifact is created.

Focused C005 result: `37 passed`; exit `0`.
Consent/candidate audit result: `19 passed`; exit `0`.
