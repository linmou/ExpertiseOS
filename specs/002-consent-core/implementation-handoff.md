# C002 Consent Core Implementation Handoff

**Intent**: Give the integration owner concise, reproducible evidence that C002 implements the approved consent boundary and is ready for dependency-gated promotion.

## Implemented Scope

- Explicit immutable domain records and lifecycle enums with validation and no dataclass field defaults.
- Volatile candidate and decision-grant stores, including session ownership, one grant per actual user event, decline, edit invalidation, unrelated-decision expiry, and restart loss.
- Canonical SHA-256 approval binding over displayed semantic content and expected versions.
- Guarded create, revision, relationship, retirement, and grouped conflict-resolution operations through C001's explicit backend methods.
- Exact approved-result validation, versioned read-back, optimistic conflict handling, deterministic grouped child operation IDs, retry reconciliation, and truthful commit statuses.
- SQLite persistence limited to completed `approval_receipts`; candidate content and suppression state are never serialized.

## Verification Evidence

Environment: branch `002-consent-core`, Python 3.12.10, starting integration receipt `fbb164b6b5b5d79d874250c2007565ab8dc05c4b`.

- Component selection: `.venv-arm64/bin/python -m pytest tests/unit/test_domain_models.py tests/unit/test_candidate_lifecycle.py tests/unit/test_approval_gate.py tests/unit/test_exact_write.py tests/unit/test_decline_no_persistence.py tests/unit/test_stale_approval.py tests/unit/test_cross_session_approval.py tests/unit/test_version_conflict.py tests/unit/test_relationship_approval.py tests/unit/test_provenance.py tests/unit/test_approval_receipts.py tests/integration/test_consent_commit_flow.py` -> 51 passed, exit 0.
- Repository suite: `.venv-arm64/bin/python -m pytest` -> 92 passed, exit 0.
- Type check: `.venv-arm64/bin/mypy --strict src/expertiseos/domain/models.py src/expertiseos/domain/candidate_store.py src/expertiseos/domain/errors.py src/expertiseos/approval/gate.py src/expertiseos/knowledge/service.py src/expertiseos/state/sqlite.py` -> success in 6 files, exit 0.
- Lint: `.venv-arm64/bin/ruff check` over all C002 production and test files -> all checks passed, exit 0.
- Format: `.venv-arm64/bin/ruff format --check` over all C002 production and test files -> 22 files already formatted, exit 0.
- Import smoke: imported `ApprovalGate`, `DecisionGrantStore`, `CandidateStore`, `KnowledgeService`, and `SQLiteState` -> `consent-core-import-ok`, exit 0.
- Ownership and whitespace: `git diff -- src/expertiseos/knowledge/backend.py tests/fakes.py` produced no diff; `git diff --check` exited 0.

The tests exercise actual proposal/grant/gate/service integration, zero-write adversarial cases, unique-marker absence in an independently opened SQLite database and backend search, stale contenders, exact receipt failure/retry, post-write timeout replay, consistent backend tampering, and per-child grouped validation.

## Corrections During Verification

- Enforced one decision grant per adapter/session/user-event reference and updated multi-decision fixtures to use distinct event identities.
- Added comparison of backend mutation results to approved content before accepting exact read-back, covering a backend that consistently stores and returns altered content.
- Added per-effect approved-result validation for grouped operations.
- Replaced private SQLite connection inspection and dynamic test imports with public, independent checks.

## External Assumptions

- C001 explicit backend methods preserve canonical `operation_id` results and reject divergent reuse.
- Hosts produce `DecisionObservation` only from an unambiguous actual-user event and supply stable adapter, session, and user-event references.
- Integration promotion preserves C001 commit `f7b1eb59a7d1837c367095e195ea7a42ead20098` beneath this component.

## Integration Boundaries

- C003 must use `KnowledgeService`; it cannot expose C001 backend mutation methods directly to hosts.
- C004 may extend the forward-only SQLite schema while preserving `approval_receipts` semantics and volatile candidates/grants.
- C005 and C006 register grants only from actual-user `DecisionObservation` values bound to the displayed proposal.
- C007 and C008 must preserve `CommitStatus`, canonical `operation_id`, and retry/idempotency behavior.

## Known Limitations

- Grouped operations use deterministic sequential backend calls; C002 reports partial failure truthfully but cannot provide cross-call rollback through the C001 contract.
- Retry reconciliation is process-local until a completed receipt exists; a restart after backend success but before receipt completion relies on replay through the same canonical `operation_id`.
- This component does not claim production host, Basic Memory, retrieval, learner-state, export, or final-product coverage.

## Intentionally Excluded Files

- `src/expertiseos/knowledge/backend.py`
- `tests/fakes.py`
- Shared implementation-status documentation owned by integration
