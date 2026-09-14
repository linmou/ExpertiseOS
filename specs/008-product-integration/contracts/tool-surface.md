# Contract: Host-Neutral Tool Surface

**Intent**: Define the minimum host-facing operations while preserving upstream authorization and ownership boundaries.

## Read Operations

| Operation | Required Inputs | Result |
|---|---|---|
| `search_knowledge` | query, limit, optional scope | Bounded approved matches with IDs, versions, provenance, conflicts, learner state, and degraded status |
| `get_knowledge` | object ID, optional version | One approved object projection or typed not-found result |
| `inspect_learning_state` | object ID | Promoted C004 evidence and summary projection |
| `inspect_controls` | none | Effective controls and reason for the current behavior mode |
| `inspect_capabilities` | adapter/session | Proven host and service capabilities |
| `health` | none | Service/backend/index status without sensitive content |

## Proposal and Decision Operations

| Operation | Required Inputs | Boundary |
|---|---|---|
| `propose_create_knowledge` | session, adapter, exact candidate payload and approved source scope | Creates volatile proposal only |
| `propose_revision` | session, adapter, object ID/version, exact revised payload | Creates volatile proposal only |
| `propose_relation_change` | session, adapter, relation delta and affected versions | Creates volatile proposal only |
| `propose_learning_evidence` | session, adapter, evidence and proposed state | Creates volatile proposal only |
| `decline_proposal` | session, adapter, proposal ID | Expires/declines volatile proposal; no candidate persistence |
| `commit_proposal` | session, adapter, proposal ID, decision-grant reference, expected versions, idempotency key | Delegates to C002 guarded commit; no boolean approval input |

Only promoted adapters can register a real user decision. The MCP/model surface cannot manufacture a `DecisionGrant`.

## Control and Ownership Operations

| Operation | Required Inputs | Boundary |
|---|---|---|
| `propose_control_change` | session, adapter, exact control delta | Guarded semantic/user-state proposal |
| `propose_retire_or_delete` | session, adapter, object/version and requested action | Guarded ownership proposal |
| `export_data` | requested scope and destination chosen through promoted ownership contract | Delegates to C007; exports approved in-scope data only |
| `restore_data` | validated export reference and collision policy from C007 | Delegates to C007 guarded restore contract |
| `remove_deferred_activity` | exact approved activity reference | Uses promoted C004/C002 state-change contract |

## Common Result Contract

Every operation returns a `ToolResult` with `status`, bounded `data`, optional `error_code`, and accurate `message`. Write success is returned only after the promoted service confirms durable canonical state and the corresponding receipt. Conflict, degraded, unavailable, and rejected are distinct.

## Forbidden Surface

- No Basic Memory create/update/delete or raw SQLite operation.
- No generic execute command.
- No `approved`, `user_approved`, or equivalent caller assertion.
- No operation that marks mastery directly.
- No tool that changes behavior because retrieved content requests it.
- No vault-wide read when bounded query/inspection satisfies the task.
