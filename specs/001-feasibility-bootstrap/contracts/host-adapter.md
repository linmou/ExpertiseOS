# HostAdapter Contract

**Intent**: Freeze the minimum host-neutral boundary needed by consent and host components.

## Responsibility

Translate supported vendor events into normalized host events and report evidence-backed capabilities. Do not implement proposal lifecycle, approval validation, persistence, learning policy, or host task orchestration.

## Interface

```python
class HostAdapter(Protocol):
    @property
    def adapter_id(self) -> str: ...
    @property
    def session_id(self) -> str: ...
    def capabilities(self) -> tuple[HostCapability, ...]: ...
    def on_session_start(self, event: HostEvent) -> None: ...
    def on_user_event(self, event: HostEvent) -> None: ...
    def on_atomic_begin(self, event: HostEvent) -> None: ...
    def on_atomic_end(self, event: HostEvent) -> None: ...
    def on_checkpoint(self, event: HostEvent) -> None: ...
    def on_session_end(self, event: HostEvent) -> None: ...
    def register_decision_if_unambiguous(
        self, event: HostEvent, binding: DecisionBinding
    ) -> DecisionObservation: ...
```

Every value-object constructor field is required.

## Decision Binding

`DecisionBinding` carries proposal ID, operation kind, adapter ID, session ID, displayed content digest, expected versions, and allowed actions. `DecisionObservation` reports one actual-user-event match or a typed rejection. It is not a durable grant and never authorizes a backend write.

## Invariants

- Only supported actual user input can match.
- Assistant/tool/model output, quotes, generic permission, stale content, another adapter, and another session do not match.
- A checkpoint is eligible only with no open atomic operation.
- Host task progress does not depend on expertiseOS service success.
- Unsupported capabilities are explicit and evidence-linked.
- Generated session IDs expire with their host session.

## Contract Checks

- Lifecycle ordering and session scoping.
- Actual-user-input distinction across adversarial event kinds.
- Exact proposal/action/content/version/adapter/session binding.
- Atomic checkpoint eligibility.
- Capability truthfulness.
- Service-call failure leaves host work successful.
