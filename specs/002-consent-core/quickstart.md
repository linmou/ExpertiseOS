# Quickstart: Verify Consent Core

**Intent**: Give implementers and integrators one concise path to prove exact approval, negative persistence, concurrency, and interrupted-write behavior.

## Prerequisites

- C001 package/bootstrap and frozen host/backend fake contracts are integrated.
- Python 3.12 development environment is active.
- No production host or Basic Memory process is required for this component check.

## Verification Sequence

1. Run candidate/domain tests and verify legal transitions, illegal transitions, restart loss, blank-content rejection, required subjects, stable IDs, and explicit constructor fields.
2. Run approval tests and verify all forged, replayed, cross-proposal, cross-session, cross-adapter, changed-digest, and stale-version cases produce no mutation or receipt.
3. Run the exact commit flow against the conforming fake backend and temporary SQLite state store. Verify canonical write, exact read-back, receipt, grant consumption, and approved candidate ordering.
4. Inject a backend failure and verify no receipt or Saved result.
5. Inject receipt failure after backend success, retry with the same `operation_id`, and verify exactly one object/version and one receipt.
6. Run revision, relationship, contradiction-coexistence, provenance, retirement, and direct-save boundary scenarios.
7. Prepare learning-evidence, control-change, and delete proposals from actual-user decisions. Verify preparation performs no backend/state mutation or receipt write, then simulate trusted downstream success and verify completion ordering, exact replay, divergent rejection, and receipt-failure retry.
8. Run all component tests, mypy for modified modules, and repository static checks.

## Required Evidence

- Targeted and full commands exit zero.
- The integration test passes the actual `PendingOperation` and `DecisionGrant` through the real approval gate and `KnowledgeService` into the fake backend and real temporary SQLite store.
- A unique marker used in decline/expiry/restart cases is absent from the SQLite database and fake backend records.
- Reconciliation evidence reports one backend mutation result and one matching approval receipt after a duplicate retry.
- Delegated preparation produces no receipt or durable mutation; completion uses the prepared authorization and exact downstream affected versions.
- Type checking covers every modified production module.

## Stop Conditions

- Any unauthorized or stale case mutates state.
- Any non-committed result can be mistaken for Saved.
- Candidate content appears in SQLite, files, logs, or other component-controlled durable artifacts.
- Retrying the same `operation_id` creates another object/version or a divergent receipt.
- A delegated completion succeeds without same-instance preparation and downstream exact read-back.
- Any C002 implementation adds a generic backend mutation method instead of calling C001's explicit methods with `operation_id`.
