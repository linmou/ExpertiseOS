# Verification Quickstart: Learner Evidence and Controls

**Intent**: Give implementers a short, reproducible route through the component's highest-risk behavior and integration boundary.

## Prerequisites

- C002 approval/state promotion SHA is merged into this branch.
- C003 retrieval contract promotion SHA is merged for approved object/version/conflict facts.
- Python 3.12 project environment is installed through the repository's documented setup.

## Focused Verification

```bash
pytest tests/unit/test_learner_evidence.py tests/unit/test_mastery_transitions.py tests/unit/test_autonomy_heuristic.py
pytest tests/unit/test_reflection_counting.py tests/unit/test_effort_limit.py tests/unit/test_target_vs_fatigue.py tests/unit/test_pause_disable.py
pytest tests/unit/test_deferred_learning.py tests/unit/test_scope_exclusions.py tests/unit/test_inspection.py
pytest tests/contract/test_learning_boundaries.py
pytest tests/integration/test_learning_state_sqlite.py
mypy src/expertiseos/learning tests/unit tests/contract tests/integration/test_learning_state_sqlite.py
```

Use the repository's final established command names if bootstrap selects wrappers around these tools.

## Required Evidence

1. A saved object with no qualifying evidence inspects as `new`.
2. Assistant-only, unknown-contribution, self-report, and rejected evidence do not advance mastery.
3. Only pass evidence advances; partial, fail, and insufficient evidence remain inspectable with zero contribution.
4. Valid threshold configurations preserve monotonic state selection; invalid values are rejected.
5. The complete autonomous fixture passes; removing each condition individually withholds `autonomous`, regardless of numeric threshold settings.
6. All overlapping control inputs resolve in documented precedence and expose the correct four permissions.
7. Target completion, fatigue, pause, and disable remain behaviorally distinct across period rollover.
8. Duplicate evidence/reflection/effort IDs do not duplicate state after retry, restart, or alternate-host delivery.
9. Deferred activity with free-form unapproved content or unresolved references is rejected.
10. SQLite integration proves migrations, restart, threshold persistence, stale version rejection, global counts, and bounded inspection.

## Handoff Verification

C008 must pass the actual approved object/version from C003 and the actual approval receipt/state implementation from C002 through C004 in the same integration run. Replacing either boundary with a synthetic fixture does not establish the orchestration edge.
