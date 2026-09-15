# C004 Verification: Learner Evidence and Learning Controls

**Intent**: Preserve reproducible implementation evidence, dependency provenance, boundary limits, and integration work remaining after the C004 local gate.

## Metadata

| Field | Value |
|---|---|
| Component branch | `004-learning-controls` |
| Baseline promotion | `166f196638e66e4aea324ee12d117507963e7629` |
| Receipt merge | `a951492366e1d4e1245d2b31bbd197f7ef99bbab` |
| Runtime | CPython 3.12.10 in `.venv` |
| Platform | macOS, local worktree |
| Verification date | 2026-09-14 |

The receipt gate before implementation reported 5/5 tests passed and a passing health smoke. C004 consumed the actual promoted `ApprovalReceipt`, `LearnerState`, and `SearchResult` types.

## Implemented Behavior

- `learning/evidence.py`: explicit-field evidence records, C002 receipt and C003 object/version/scope validation, pass-only advancement, configurable monotonic thresholds, deterministic state summary, autonomous safeguards, and bounded inspection.
- `learning/controls.py`: explicit daily/weekly defaults, period keys, exact control precedence, separate permissions, fatigue intent, highest-only effort, idempotent progress functions, literal scope exclusions, minimal deferred references/removal, and bounded inspection.
- No SQLite migration, public service/MCP wiring, host parser, background process, scoring model, policy engine, or summary cache was added.

## Behavioral Evidence

| Requirement area | Key test evidence |
|---|---|
| Pass-only mastery | Partial, fail, and insufficient evidence remain inspectable and produce zero advancement; save/retrieval/model-only/unknown contribution cannot qualify. |
| Thresholds | Explicit default `1,1,1,1,2`; alternate positive nondecreasing values work; zero, decreasing, and autonomous-below-two values fail. |
| Autonomous | Complete case passes; missing pass count, independence, task, session, transfer, contradiction clearance, or agreement individually withholds autonomous. |
| Evidence applicability | Wrong ID/version/scope remains excluded; matching promoted receipt and search result pass the boundary contract. |
| Controls | Disabled, pause, fatigue, target, active precedence and four permission outputs pass, including overlap and expiry. |
| Period/effort | Local timezone daily/weekly keys, weekly 3 preset, 0/0.25/1/2 highest-only effort, duplicate event, and exact limit pass. |
| Reflection/deferred | Qualification conditions, linked-output single count, retry idempotency, approved-reference-only deferment, later active foreground offer, and explicit removal pass. |
| Structural safety | All 16 new dataclasses have no definition defaults; bounded inspection and no deferred content field are asserted. |

## Commands and Results

| Command | Result |
|---|---|
| `uv sync --prerelease allow --extra dev` | PASS; resolved environment and installed the local package plus dev tools. |
| `.venv/bin/pytest <C004 unit and contract files> -q` | PASS; 64 passed in 0.10s after final edge additions. |
| `.venv/bin/pytest -q` | PASS; 182 passed, 3 expected G0 skips in 0.49s. |
| `.venv/bin/mypy --strict src tests` | PASS; no issues in 75 source files. |
| `.venv/bin/ruff check src tests` | PASS; all checks passed. |
| `.venv/bin/ruff format --check src tests` | PASS; 75 files already formatted. |
| `.venv/bin/python -c '<C004 import/default smoke>'` | PASS; `learning smoke: ok`. |

Initial environment diagnostics: the PATH `pytest` process terminated with signal 11. An initial `uv run` without prerelease mode could not resolve Basic Memory's pinned `fastmcp==4.0.0b1`. The informed correction was one environment sync using the repository-required `--prerelease allow`; no code or experiment behavior changed to hide either failure.

## Changed Factors

| Factor | Change and purpose |
|---|---|
| Mastery outcome | Only approved `pass` contributes; other outcomes remain inspection-only, per canonical human decision. |
| Threshold configuration | Positive nondecreasing integer counts are explicit at instantiation; defaults are `1,1,1,1,2`. |
| Autonomous evaluation | Numeric count is configurable but all non-numeric PRD safeguards remain mandatory. |
| Evidence data | Summary is scoped to exact approved object version and requested scope. |
| Control evaluation | One deterministic precedence function returns separate behavior permissions. |
| Evaluation method | Focused unit/contract suite plus full repository, strict typing, lint, format, and import smoke. |

## Integration-Owned Work

Integration accepted the SQLite schema/API request in implementation commit `38d170c` after explicit component merge `d818f59`.

- `tests/integration/test_learning_state_sqlite.py` covers fresh and legacy migration, restart, actual approval-receipt binding, version/scope filtering, unavailable-state failure, configurable threshold persistence, stale control versions, global duplicate event handling, transaction rollback, bounded reads, and approved-reference-only deferred schema.
- `tests/integration/test_approved_learning_state_handoff.py` consumes an actual C002 gate/grant/receipt result in C004 persistence and mastery summary.
- `tests/integration/test_retrieval_learning_handoff.py` consumes an actual C003 retrieval result in C004 validation, summary, and inspection.
- `rtk .venv-arm64/bin/python -m pytest -q tests/integration/test_learning_state_sqlite.py tests/integration/test_approved_learning_state_handoff.py tests/integration/test_retrieval_learning_handoff.py tests/unit/test_approval_receipts.py`: PASS; 10 passed in 0.09 seconds.
- `rtk .venv-arm64/bin/python -m mypy src tests`: PASS; 78 source files checked.
- `rtk .venv-arm64/bin/python -m ruff check src tests`: PASS.
- `rtk .venv-arm64/bin/python -m ruff format --check src tests`: PASS; 78 files formatted.

Task T042 remains open until the green C004 promotion SHA is delivered downstream:

- C008 must wire the tested C004 functions to the public service/MCP and real C005/C006 host control paths.
- The integration owner must record actual producer-to-consumer edge evidence and promotion SHA.

## Requirement Trace

- FR-001 through FR-008 and FR-025: evidence, pass-only mastery, thresholds, version/scope, and autonomous tests.
- FR-009 through FR-020: period, effort, reflection, control, exclusion, and inspection tests.
- FR-021 through FR-023: deferred and idempotent pure-intent tests.
- FR-024: boundary contract tests plus open durable SQLite integration tasks.
- AT-07/AT-09/AT-10/AT-11: deterministic component behavior is locally covered; public real-service acceptance remains C008-owned.
- AT-12/AT-15 portions: duplicate pure events and hostile control separation are covered locally; real cross-host/service paths remain integration-owned.

## Risks

- Durable evidence/control/deferred storage is intentionally unavailable until C002's shared SQLite owner implements the accepted request.
- C003 reports conflicts as IDs; integration must ensure those conflicts are relevant to the requested mastery scope before setting the boolean fact.
- Scope exclusion enforcement depends on C005/C006 checking before observation and C003/C008 checking before retrieval return.

## Final Scope Audit

The owned source imports no SQLite implementation, Basic Memory backend, knowledge service, or host adapter. Text scan found no background worker, scheduler, psychometric score, policy engine, or summary-cache implementation. The only durable-boundary operation is validation of actual promoted C002/C003 record types before an integration-owned state write.
