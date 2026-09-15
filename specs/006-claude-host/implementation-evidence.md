# Claude Code Adapter Implementation Evidence

**Intent**: Record the exact upstream state, verification results, and unsupported live-host limits for C006.

## Provenance

- Component branch: `006-claude-host`
- Locally verified implementation commit: `0dbabb2a6dd4630a5f9ae01bb078b2c1e6b57137`
- Implementation baseline: `044bad2a0bd15b4abce4a240d6b4e80444be427d`
- Integrated C001-C004 promotion: `649cb66533e78901a71a0a1c7fbd268cb9929fe2`
- C004 promotion received: `633961d62a63ff761b992df768b1c04b173e2cd4`
- Verification date: 2026-09-14
- Verification runtime: Python 3.12 from the integration `.venv-arm64`

The promoted contracts provide C001 host events and decision bindings, C002 volatile proposal/grant/commit handling, C003 bounded retrieval responses, and C004 resolved permissions plus exclusions. C006 consumes those contracts without direct backend or SQLite access and without recreating control precedence.

## Pinned Host Evidence

- Claude Code: `2.1.241`, build `c87e2742fc9a`
- Host: macOS `15.1.1` build `24B91`, `arm64`, default permission mode
- Source: `specs/001-feasibility-bootstrap/evidence/claude-code/host-feasibility.md`
- Passed evidence: installed CLI, public plugin commands, public hook schema, session and actual-user fields
- Not run: live plugin activation, configuration preservation, uninstall, lifecycle ordering, service-failure delivery, and authenticated six-step decision capture

Supported capability matrix for this exact environment:

| Capability | Available | Reason |
|---|---:|---|
| `can_read` | true | Passed installed-interface evidence and shared-service contract |
| `can_search` | true | Passed installed-interface evidence and bounded shared retrieval |
| `can_validate_user_decisions` | false | Authenticated live six-step fixture not run |
| `can_write` | false | Requires passed live decision validation as well as write evidence |
| `can_observe_atomic_boundaries` | false | Live event ordering not run |
| `can_auto_activate` | false | Configuration-preserving activation/removal not run |

The adapter exposes public `claude plugin install` and `claude plugin uninstall` argument vectors, but does not claim automatic activation or configuration preservation without live evidence.

## Verification

The command output below is the retained test log for this component.

| Gate | Command | Result |
|---|---|---|
| Focused format | `.venv/bin/ruff format src/expertiseos/hosts/claude_code.py tests/contract/test_claude_code_adapter.py tests/integration/test_claude_code_service.py` | exit 0; final run formatted 1 file |
| Focused lint | `.venv/bin/ruff check src/expertiseos/hosts/claude_code.py tests/contract/test_claude_code_adapter.py tests/integration/test_claude_code_service.py` | exit 0; all checks passed |
| Focused types | `.venv/bin/mypy src/expertiseos/hosts/claude_code.py tests/contract/test_claude_code_adapter.py tests/integration/test_claude_code_service.py` | exit 0; no issues in 3 files |
| Contract | `PYTHONPATH=src /Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration/.venv-arm64/bin/python -m pytest tests/contract/test_claude_code_adapter.py -q` | exit 0; 39 passed in 0.07s |
| Integration | `PYTHONPATH=src /Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration/.venv-arm64/bin/python -m pytest tests/integration/test_claude_code_service.py -q` | exit 0; 10 passed in 0.07s |
| Durable safety selection | `PYTHONPATH=src /Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration/.venv-arm64/bin/python -m pytest tests/integration/test_claude_code_service.py -q -k 'session_end or unproven_live_save or stale_concurrent_revision or service_outage'` | exit 0; 4 passed, 6 deselected in 0.03s |
| Full tests | `PYTHONPATH=src /Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration/.venv-arm64/bin/python -m pytest -q` | exit 0; 244 passed in 99.76s |
| Full format | `/Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration/.venv-arm64/bin/ruff format --check src tests` | exit 0; 82 files already formatted |
| Full lint | `/Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration/.venv-arm64/bin/ruff check src tests` | exit 0; all checks passed |
| Full types | `PYTHONPATH=src /Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration/.venv-arm64/bin/python -m mypy src tests` | exit 0; no issues in 82 source files |
| Import | `PYTHONPATH=src /Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration/.venv-arm64/bin/python -c 'import expertiseos; import expertiseos.hosts.claude_code'` | exit 0 |
| Smoke | `PYTHONPATH=src /Users/admin/Documents/GitHub.nosynchr/expertiseOS_full-worktrees/expertiseos-mvp/integration/.venv-arm64/bin/python -m expertiseos` | exit 0; `{"service": "expertiseos", "status": "bootstrap-ready"}` |

The first direct-save test run exposed that `Save: content` was not classified as a Save action. The parser was corrected to recognize only the explicit nonempty `Save: <content>` form. Malformed retrieval and Saved-status boundaries were then added. The final focused suite passed 49 tests, and the final full suite passed 244 tests.

## Sanitized Boundary Evidence

| Input | Output |
|---|---|
| Exact environment plus passed read/search evidence | Read/search true; all live-dependent capabilities false |
| Actual user `Save` with production evidence | `action_not_allowed`; no grant, receipt, or durable marker |
| Test-only exact `Save` with matching binding | Real C002 path commits once; repeated commit returns the same record |
| Test-only `Edit: revised exact text` | Digest changes and a fresh Save event is required |
| Test-only `Save: direct exact text` | Normal C002 direct-proposal/grant path commits the exact text |
| Changed expected version before commit | `conflict`; concurrent value is not overwritten |
| Session end with an unresolved proposal | C002 proposal expires; late Save is rejected |
| Service exception during retrieval | No retrieval result; ordinary host task result remains available |
| Actual C003 retrieval response | Stable ID/version and untrusted-data labeling reach the adapter unchanged |

Synthetic decision/write evidence is test-only and cannot promote the production capability matrix. No authenticated live-host input/output pairs exist yet, so persistent writes remain disabled.

## Open Gates

- Run configuration-preserving activation, health, and uninstall on the pinned host before enabling automatic activation.
- Add and run the authenticated marker-gated live-host fixture before enabling atomic-boundary observation, decision validation, or persistent writes.
- Run the live-file-inclusive Ruff command and restart-specific durable-store scenario once that fixture exists.
