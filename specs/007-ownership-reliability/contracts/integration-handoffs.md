# Contract: C007 Integration Handoffs

**Intent**: State real producer-consumer capabilities required from C002-C004 and delivered to C008.

## C002 Approved-State Producer

```text
iter_approval_receipts() -> approved receipt records
get_operation(operation_id) -> content-free operation state
put_operation_state(operation_state) -> content-free state only
reconcile_receipt(operation_id, idempotency_key, canonical_ref) -> receipt result
commit_retire(approved_operation) -> mutation result
commit_delete(approved_operation) -> mutation authorization/result
```

C002 owns SQLite and guarded knowledge-service edits. Tests reject semantic content in operation state and prove reconciliation cannot duplicate canonical writes.

## C003 Canonical Backend Producer

```text
snapshot_approved() -> stable ordered approved records
inspect_identity(id) -> version and canonical digest
restore_approved(records, operation_id) -> per-record result
delete_scoped(scope, operation_id) -> per-target result
inspect_index_health() -> search health
rebuild_index_from_approved(operation_id) -> rebuild result
keyword_search(query, limit, hints?) -> bounded approved results
controlled_locations() -> canonical/index location descriptors
```

C003 owns backend/index implementation. Snapshots are deterministic. Rebuild emits no approval or learning event.

## C004 Learner/Control Producer

```text
snapshot_learning_state() -> approved evidence/summaries/controls/progress/deferred records
restore_learning_state(records, operation_id) -> per-record result
delete_learning_scope(scope, operation_id) -> evidence/deferred cleanup result
controlled_locations() -> learner/control location descriptors
```

C004 owns learner/control and SQLite implementation. Restored records remain bound to valid approved knowledge IDs/versions.

## C007 Output to C008

C008 consumes export/restore/delete/uninstall/recovery results and explicit search health. C008 preserves status distinctions and owns host registration/service shutdown actions.

## Required Edge Tests

- C002 canonical-success/receipt-failure output enters C007 reconciliation and yields exactly one C002 receipt.
- C003 approved snapshot and C004 state enter one export, then restore through the same producer contracts with exact references.
- C007 deletion invokes actual C003/C004 cleanup; the audit reads their actual controlled locations.
- C003 index failure enters C007 degradation and actual keyword results reach C008 tagged `untrusted_data`.
- C008's network-denied scenario calls actual C007/C003 local paths and records no remote dependency.
