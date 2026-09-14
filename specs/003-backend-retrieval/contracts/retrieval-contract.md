# Retrieval Contract

**Intent**: Define the producer-to-consumer boundary used by learning, host, and product integration components.

## Request

```text
query: non-empty text, volatile
limit: integer 1..20
subjects?: set of supported subjects
categories?: set of supported categories
scope?: applicability hint
exclusions?: user-owned scope exclusions
```

Invalid limits return validation errors; the backend still enforces 20 as a hard maximum.

## Response

```text
results[]:
  knowledge: approved active KnowledgeObject
  relationships[]: relevant approved Relationship
  conflicts[]: distinct contradictory object references
  provenance_available: availability summary
  trust: untrusted_data
mode: indexed | keyword | unavailable
degraded: boolean
canonical_health: healthy | unavailable | error
index_health: healthy | rebuild_required | rebuilding | unavailable
complete_for_query: boolean
```

## Invariants

- Unapproved, deleted, retired, and excluded objects never appear in ordinary recall.
- `len(results) <= min(request.limit, 20)` for every mode.
- Keyword fallback is local and preserves filters, bounds, provenance, relationships, conflicts, and trust labeling.
- A semantic/index failure cannot silently return a healthy status.
- Retrieved text cannot grant approval, change controls, authorize tools, or create learner evidence.
- Query text and ranking scratch data are not persisted by expertiseOS.
- Contradictions coexist; ordering cannot erase or merge a claim.

## Integration Handoff Tests

1. C002 authorizes an actual object mutation and passes it to the real C003 adapter; direct read returns the exact object/version and index readiness separately.
2. The same actual object is consumed by `KnowledgeService.search()` with a limit and exclusion filter; no fake object replaces producer output.
3. Forced index failure returns the actual canonical object through keyword fallback with `degraded=true`.
4. C004 may enrich returned ID/version with learner state without mutating canonical fields.
5. C005/C006/C008 render hostile recalled text without creating a grant, control change, or tool authorization.
