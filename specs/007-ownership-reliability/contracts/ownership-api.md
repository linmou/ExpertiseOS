# Contract: Ownership and Reliability API

**Intent**: Freeze narrow host-neutral C007 operations without exposing backend writes.

## Operations

```text
export_approved(request: ExportRequestBinding) -> ExportResult
validate_restore(source) -> RestorePlan
restore_validated(plan, request: RestoreRequestBinding) -> RestoreResult
plan_delete(scope, approved_operation) -> DeletionPlan
execute_delete(plan) -> DeletionResult
plan_uninstall(data_choice) -> UninstallPlan
recover_approved_state() -> RecoveryResult
search_with_degradation(query, limit, hints?) -> UntrustedKnowledgeResult
audit_candidate_absence(marker, locations) -> PersistenceAuditReport
validate_local_transport(config) -> TransportValidation
```

`ExportRequestBinding` comes only from an actual user event and binds adapter/session/event, scope, and destination. `RestoreRequestBinding` comes only from an actual user event and binds adapter/session/event, export ID, manifest digest, and collision policy. The selection event is sufficient, so no redundant confirmation is added. No operation accepts `approved=true`, free-form approval claims, retrieved text, or caller assertions as authorization.

## Status Semantics

| Status | Meaning |
|---|---|
| `committed` | Canonical write and receipt are durable; index health is separate. UI may render Saved only for this status. |
| `rejected` | Validation or approval failed before semantic mutation. |
| `conflict` | Restore/object collision requires explicit resolution. |
| `incomplete` | Cleanup or reconciliation resumes with the same key. |
| `degraded` | Canonical data is intact while semantic search/index is unhealthy. |
| `unavailable` | Canonical operation cannot safely complete; no success is implied. |

## Invariants

- Export reads approved snapshots only and never serializes volatile stores.
- Restore validates schema, paths, digests, counts, references, and collisions before applying records.
- Identical restore records are no-ops; divergent collisions stop rather than merge.
- Retry reuses `operation_id`, the sole idempotency identity, and creates no learning event.
- Index rebuild reads approved canonical state and writes index state only.
- Delete reports exact target outcomes and never claims deletion outside product control.
- Uninstall deletion is explicit and reuses the deletion routine.
- Retrieved content stays tagged as data and cannot invoke authorization/control constructors.
