# Integration Contract: C002-Owned SQLite Additions

**Intent**: Specify learner/control persistence required from C002 without creating a second writer for `src/expertiseos/state/sqlite.py`.

## Ownership

C002 owns migration numbering, SQL, connection lifecycle, transactions, and `src/expertiseos/state/sqlite.py`. C004 owns record validation and calculation in `learning/`. Integration applies this request only after C002 promotion.

## Logical Tables

### `learner_evidence`

Stores the fields in `data-model.md`. Required uniqueness: evidence `id`; required logical bindings: knowledge ID/version and approval receipt ID. User contribution is the exact approved bounded summary/excerpt, never an unresolved candidate payload.

### `control_state`

Stores one current settings record with optimistic `version`, explicit enable/pause/rest fields, target settings, effort limit, rest interval, timezone ID, and the five positive nondecreasing advancement thresholds. `autonomous_passes` is at least two. Threshold updates use the same approved expected-version change path as other settings.

### `period_progress`

Stores one row per period key plus reflection and effort totals. Companion uniqueness records, or equivalent unique constraints, ensure one reflection/event ID and effort/event ID is counted once globally across hosts.

### `scope_exclusions`

Stores stable ID, literal kind/value, creation time, and approval receipt. It contains no policy expressions.

### `deferred_activities` and references

Stores stable ID, bounded activity type, creation time, status, and approval receipt. A child/reference representation stores one or more approved knowledge ID/version pairs. There is no free-form content column.

## Required State Operations

```text
insert_evidence_once(validated_record)
list_evidence(knowledge_id, version?, scope?, limit)
apply_control_change(expected_version, approved_change)
read_control_state()
record_reflection_once(period_key, event_id)
record_effort_once(period_key, event_id, units)
replace_or_remove_exclusion(expected_version, approved_change)
insert_deferred_once(validated_record)
remove_deferred(expected_version, approved_change)
list_deferred(status, limit)
```

All list operations are bounded. Mutations are atomic with their uniqueness/version check and return stored records for read-back.

## Migration and Recovery Invariants

- A fresh database and an existing C002 database both reach the same schema deterministically.
- Reapplying migrations is a no-op.
- Restart preserves approved evidence, advancement thresholds, controls, progress, exclusions, and deferred references.
- No schema column or recovery journal stores pending proposal/candidate text.
- No summary cache is required for MVP; if later proven necessary, it must be regenerable from evidence.
- Transaction failure returns an error and cannot partially increment totals or claim success.

## Integration Evidence

C004 provides `tests/integration/test_learning_state_sqlite.py`; C002 or the integration owner supplies the concrete state adapter fixture. The test must cover fresh migration, restart, idempotent duplicate events, stale control version, cross-host global count, no deferred content field, and bounded inspection.
