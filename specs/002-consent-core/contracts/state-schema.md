# Contract: Consent State Schema

**Intent**: Define the minimal durable consent evidence and a stable migration boundary for downstream state additions.

## Migration Policy

- Use a small forward-only schema initializer owned by `src/expertiseos/state/sqlite.py`.
- Apply migrations transactionally and idempotently.
- Do not create candidate, pending-proposal, unused-grant, candidate-payload, or decline-suppression tables.
- C004 submits learner/control additions through this owner after component reconciliation.

## approval_receipts

```sql
CREATE TABLE approval_receipts (
    operation_id TEXT PRIMARY KEY NOT NULL,
    proposal_id TEXT NOT NULL,
    operation_kind TEXT NOT NULL,
    object_refs_json TEXT NOT NULL,
    content_digest TEXT NOT NULL,
    user_event_ref TEXT NOT NULL,
    adapter_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

`object_refs_json` is canonical JSON containing stable object IDs and committed positive versions, not knowledge content. `created_at` is an explicit UTC timestamp. The store rejects unknown operation kinds and malformed digests/object references before insertion.

## Idempotent Insert

`record_receipt(receipt)` has two valid outcomes:

1. The `operation_id` is absent: insert the exact receipt atomically.
2. The `operation_id` exists and all fields match: return the existing receipt as reconciled success.

If the `operation_id` exists with any different field, return an integrity conflict. Never overwrite an existing receipt.

## Queries

The component requires only:

```text
record_receipt(receipt) -> ApprovalReceipt
get_receipt(operation_id) -> ApprovalReceipt | None
close() -> None
```

No query returns unrelated prompt text or unapproved candidate content.
