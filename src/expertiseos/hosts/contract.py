#!/usr/bin/env python3
# Purpose: Define the host-neutral event and decision-observation contract.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable


class HostContractError(ValueError):
    """Raised when a host emits an invalid normalized event sequence."""


class EventKind(StrEnum):
    SESSION_START = "session_start"
    USER_INPUT = "user_input"
    ATOMIC_BEGIN = "atomic_begin"
    ATOMIC_END = "atomic_end"
    CHECKPOINT = "checkpoint"
    SESSION_END = "session_end"


class DecisionAction(StrEnum):
    SAVE = "save"
    EDIT = "edit"
    SKIP = "skip"
    CONFIRM_CHANGE = "confirm_change"


class DecisionRejection(StrEnum):
    NONE = "none"
    NOT_USER_INPUT = "not_user_input"
    MISSING_USER_PROVENANCE = "missing_user_provenance"
    WRONG_ADAPTER = "wrong_adapter"
    WRONG_SESSION = "wrong_session"
    AMBIGUOUS_ACTION = "ambiguous_action"
    ACTION_NOT_ALLOWED = "action_not_allowed"
    ALREADY_OBSERVED = "already_observed"
    SESSION_ENDED = "session_ended"


@dataclass(frozen=True)
class HostCapability:
    name: str
    available: bool
    evidence_ref: str
    limitation: str

    def __post_init__(self) -> None:
        if not self.name:
            raise HostContractError("capability name is required")
        if self.available and not self.evidence_ref:
            raise HostContractError("available capability requires evidence_ref")


@dataclass(frozen=True)
class HostEvent:
    event_id: str
    adapter_id: str
    session_id: str
    kind: EventKind
    occurred_at: datetime
    user_input_ref: str | None
    action: DecisionAction | None

    def __post_init__(self) -> None:
        if not self.event_id or not self.adapter_id or not self.session_id:
            raise HostContractError("event, adapter, and session identities are required")
        if self.kind is EventKind.USER_INPUT:
            if not self.user_input_ref:
                raise HostContractError("user input requires actual host provenance")
        elif self.user_input_ref is not None or self.action is not None:
            raise HostContractError("non-user events cannot carry user decision provenance")


@dataclass(frozen=True)
class DecisionBinding:
    proposal_id: str
    operation_kind: str
    adapter_id: str
    session_id: str
    content_digest: str
    expected_versions: tuple[tuple[str, int], ...]
    allowed_actions: tuple[DecisionAction, ...]

    def __post_init__(self) -> None:
        if not all(
            (
                self.proposal_id,
                self.operation_kind,
                self.adapter_id,
                self.session_id,
                self.content_digest,
            )
        ):
            raise HostContractError("decision binding identities and digest are required")
        if not self.allowed_actions:
            raise HostContractError("at least one decision action is required")
        if any(version < 1 for _, version in self.expected_versions):
            raise HostContractError("expected versions must be positive")


@dataclass(frozen=True)
class DecisionObservation:
    matched: bool
    action: DecisionAction | None
    user_event_ref: str | None
    rejection: DecisionRejection


@runtime_checkable
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
