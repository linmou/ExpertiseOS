# Data Model: Approved Knowledge Retrieval Backend

**Intent**: Define host-neutral storage and retrieval values without duplicating the upstream domain model or exposing Basic Memory internals.

## Knowledge Record

| Field | Rule |
|---|---|
| `id` | Stable expertiseOS identity; never inferred from title, path, or content. |
| `version` | Positive integer; increments for every approved semantic revision. |
| `content` | Non-blank approved semantic content. |
| `categories` | Zero or more approved knowledge categories. |
| `subjects` | One or more of domain, self, or AI. |
| `applicability_scope` | Optional approved conditions or exclusions. |
| `evidential_status` | Optional approved uncertainty/evidence label. |
| `status` | `active` or `retired`; retired is not deleted. |
| `source_refs` | Zero or more approved source references. |
| `contribution_origin` | `user`, `assistant`, or `joint`. |
| `created_at`, `updated_at` | Upstream timestamps preserved on round-trip. |
| `operation_key` | Idempotency key for the authorized mutation; not semantic content. |

Only approved records reach canonical storage. Stale expected versions cannot replace current versions. Retired records remain explicitly readable but leave ordinary recall. Deleted records and content are absent from active direct reads and search.

## Source Reference

| Field | Rule |
|---|---|
| `source_type` | One supported source kind. |
| `host`, `session_id`, `event_ref` | Optional minimal origin identifiers. |
| `artifact_locator` | Optional user-approved locator. |
| `approved_excerpt` | Optional approved excerpt, never an unrelated full prompt. |
| `date`, `checksum` | Optional traceability fields. |
| `accessibility_status` | Available or unavailable; disappearance never generates replacement evidence. |

## Relationship

| Field | Rule |
|---|---|
| `id` | Stable relationship identity. |
| `source_id`, `target_id` | Stable knowledge IDs. |
| `source_version`, `target_version` | Optional approved endpoint versions. |
| `type` | `derived_from`, `supports`, `contradicts`, `explains`, `example_of`, `applies_when`, or `depends_on`. |
| `explanation` | Optional approved semantic explanation. |
| `source_ref` | Optional approved provenance for the link. |

Duplicate delivery is idempotent by relationship identity and operation key. Missing or deleted endpoints are disclosed as unavailable rather than retargeted.

## Recall Query

| Field | Rule |
|---|---|
| `query` | Non-durable search text. |
| `limit` | Integer from 1 through 20. |
| `subjects`, `categories` | Optional inclusive filters. |
| `scope` | Optional applicability hint. |
| `exclusions` | User-defined exclusions applied before return. |

## Recall Result

| Field | Rule |
|---|---|
| `knowledge` | Current active approved record. |
| `relationships` | Relevant approved links. |
| `conflicts` | Distinct contradictory record references and conditions. |
| `provenance_available` | Availability summary derived from source references. |
| `trust` | Always `untrusted_data`. |

Learner state may be joined downstream by C004 using knowledge ID and version; it is not stored or inferred here.

## Retrieval Response

| Field | Rule |
|---|---|
| `results` | Ordered bounded recall results. |
| `mode` | `indexed`, `keyword`, or `unavailable`. |
| `degraded` | True whenever preferred local indexed retrieval was not used successfully. |
| `canonical_health` | Independent canonical-store health. |
| `index_health` | Healthy, stale/rebuild-required, unavailable, or rebuilding. |
| `complete_for_query` | False when degradation or failure makes completeness uncertain. |

## State Transitions

```text
approved create -> active version 1
active version N -> approved revise -> active version N+1
active version N -> approved retire -> retired version N+1
retired version N -> approved restore/revise -> active version N+1
active/retired -> approved delete -> absent from canonical active scope and index

index healthy -> update failure -> rebuild required
rebuild required -> successful rebuild from approved canonical state -> healthy
indexed query failure -> keyword fallback for request -> degraded response
canonical unavailable -> unavailable response; no false mutation success
```

## Backend Mapping

Mapping keys and Basic Memory paths are private to `basic_memory.py`. If C001 proves a sidecar necessary, it may contain only stable IDs, backend locators, versions, statuses, operation keys, and index state. It must not duplicate canonical knowledge content, source excerpts, or candidate/query text.
