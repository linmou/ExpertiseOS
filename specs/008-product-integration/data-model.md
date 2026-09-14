# Data Model: Product Integration and Acceptance

**Intent**: Define C008's transient request, response, fixture, and evidence shapes without duplicating upstream durable domain models.

## ToolRequest

Represents one host-neutral call into the composition service.

| Field | Rules |
|---|---|
| `operation` | One name from the public tool contract |
| `adapter_id` | Required for session-bound operations |
| `session_id` | Required for proposal, decision, and commit operations |
| `payload` | Operation-specific validated inputs; cannot contain a boolean approval shortcut |
| `operation_id` | Required for mutations and used as their sole idempotency identity |
| `request_id` | Optional read-only correlation identity; never used for mutation idempotency or authorization |

Validation: unknown fields and operations fail explicitly; mutation requests must carry the exact upstream proposal/decision references required by the guarded service.

## ToolResult

Represents a consistent response to a host.

| Field | Rules |
|---|---|
| `status` | `ok` for successful reads; `committed`, `rejected`, `conflict`, `failed`, `incomplete`, `degraded`, or `unavailable` as applicable |
| `data` | Bounded operation result; absent on rejection where disclosure would be unsafe |
| `error_code` | Stable machine-readable reason for non-`ok` status |
| `message` | Concise user-facing explanation; never claims a write succeeded before durable confirmation |
| `capabilities` | Included when behavior depends on proven host/service capability |

Only `committed` may produce a Saved user-facing result. `ok` never represents a mutation commit. `failed` is a completed failure; `incomplete` means reconciliation is required before success or retry can be reported.

## CapabilityView

Read-only projection of upstream host capabilities: `can_read`, `can_search`, `can_validate_user_decisions`, `can_write`, `can_observe_atomic_boundaries`, and `can_auto_activate`. `can_write` is false unless decision validation is proven.

## ReferenceScenario

| Field | Rules |
|---|---|
| `scenario_id` | Stable `A` through `D` identifier |
| `title` | Human-readable scenario name |
| `requirements` | Linked FR/NFR identifiers |
| `acceptance_tests` | Linked AT identifiers |
| `initial_approved_state` | Approved objects, controls, and versions only |
| `events` | Ordered normalized host and user events |
| `expected_visible_results` | Ordered user-visible checkpoints and outcomes |
| `expected_persistent_delta` | Exact approved additions/changes/removals; must exclude candidate payloads |
| `expected_volatile_end_state` | Remaining or expired proposals/grants |

Scenario fixtures contain no executable instructions and do not replace upstream implementations.

## AcceptanceCase

| Field | Rules |
|---|---|
| `at_id` | Exactly one of AT-01 through AT-16 |
| `applicable_environments` | Automated integration, Codex, Claude Code, cross-host, adversarial, or offline |
| `fixture_ids` | Versioned inputs used by the case |
| `producer_consumer_edges` | Actual promoted handoffs exercised |
| `assertions` | Deterministic observable and state-integrity conditions |
| `quality_class` | Consent, privacy, state integrity, behavior, reliability, ownership, or locality |

## AcceptanceEvidence

| Field | Rules |
|---|---|
| `schema_version` | Version of the evidence contract |
| `at_id` | Acceptance case identifier |
| `tested_sha` | Immutable integration or component commit tested |
| `command` | Exact command executed |
| `exit_code` | Process exit status |
| `started_at` / `finished_at` | UTC timestamps |
| `environment` | OS, Python, dependency, host/model, and network mode metadata as applicable |
| `fixture_versions` | Exact fixture/corpus identities |
| `edge_artifacts` | Producer outputs consumed by downstream calls |
| `result` | `pass`, `fail`, or `not_applicable` with a reason |
| `output_path` | Durable log/report path containing no unapproved candidate content |

The integration review maps `tested_sha` to a later promotion SHA after post-test audit and smoke gates pass; the test-run record does not predict or require that promotion identity.

## State and Ownership

C008 entities are input/output or test evidence only. Canonical knowledge, proposals, grants, receipts, learner evidence, controls, deferred activities, export data, and recovery state remain defined and owned by C002-C007.
