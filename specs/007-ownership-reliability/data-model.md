# Data Model: Ownership and Reliability

**Intent**: Define only C007-owned or exchanged records while leaving canonical knowledge and learner/control schemas with upstream owners.

## PortableExportManifest

| Field | Rule |
|---|---|
| `schema_version` | Required supported integer; MVP writes `1`. |
| `export_id` | Required stable identifier for the bundle. |
| `created_at` | Required UTC timestamp. |
| `source_product_version` | Required installed expertiseOS version/commit. |
| `files` | Required record descriptors with paths and digests. |

Paths are relative, normalized, unique, and cannot escape the bundle. Digests cover exact bytes. No candidate or grant section exists.

## ExportRecordDescriptor

| Field | Rule |
|---|---|
| `record_type` | Knowledge, relationship, source reference, receipt, learner record, control, progress, or deferred activity. |
| `path` | Manifest-listed JSONL/Markdown relative path. |
| `count` | Non-negative number matching parsed records. |
| `digest` | Digest matching exact file bytes. |

## RestorePlan

| Field | Rule |
|---|---|
| `export_id` | Validated manifest export ID. |
| `applicable_records` | Missing local identities safe to apply. |
| `identical_records` | Same ID/version/digest; no-op. |
| `collisions` | Same identity with non-identical state. |
| `validation_errors` | Schema, digest, count, path, reference, or semantic errors. |

State: `unvalidated -> valid | rejected`; only collision-free `valid` enters `applying -> complete | repair_required`. `repair_required` is allowed only when approved records are restored but index rebuilding fails.

## DeletionPlan

| Field | Rule |
|---|---|
| `operation_id` | Upstream-approved operation and idempotency anchor. |
| `object_refs` | Exact stable IDs and expected versions. |
| `content_targets` | Enumerated canonical, revision, excerpt, and index locations. |
| `relationship_actions` | Remove or convert to disclosed content-free unavailable reference. |
| `evidence_actions` | Remove content in approved scope while preserving allowable integrity fields. |
| `deferred_actions` | Remove activities invalidated by deleted references. |
| `external_limits` | Known copies outside product control. |

State: `approved -> applying -> complete | incomplete`; retry resumes incomplete targets with the same key.

## OperationRecord

| Field | Rule |
|---|---|
| `operation_id` | Unique approved operation identity. |
| `idempotency_key` | Stable key for the operation. |
| `operation_kind` | Restore, delete, receipt reconciliation, or index rebuild. |
| `object_refs` | IDs/versions only; never content or excerpts. |
| `phase` | Valid phase for the operation kind. |
| `status` | Pending, complete, incomplete, or repair required. |
| `created_at` / `updated_at` | UTC timestamps. |

Operation records reject payload, content, excerpt, query, and grant fields.

## SearchHealth

`mode` is semantic, keyword degraded, or unavailable; `canonical_available` and `repair_required` are explicit; `reason_code` is content-free.

## UntrustedKnowledgeResult

Contains bounded approved items, constant trust label `untrusted_data`, applied limit, and `SearchHealth`. It has no path to decision-grant, tool-authorization, mastery, or control constructors.

## PersistenceAuditReport

Contains fixture ID, marker digest, enumerated controlled locations and outcomes, pass/fail, excluded host-owned locations, and product/backend/index versions. The marker is runtime-only.

## BenchmarkResult

Contains operation, samples, p50/p95/p99, units, threshold, verdict, warm-up count, corpus seed/size/shape, hardware, OS, Python, Basic Memory, index configuration, command, and Git commit. Reproduction metadata contains no user content.

## Upstream Records

C007 consumes but never duplicates `KnowledgeObject`, `Relationship`, `SourceReference`, `ApprovalReceipt`, `LearnerEvidence`, learner summary, control settings, period progress, or deferred activity records.

