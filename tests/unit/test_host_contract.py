#!/usr/bin/env python3
# Purpose: Test src/expertiseos/hosts/contract.py host provenance and lifecycle boundaries.

from __future__ import annotations

from dataclasses import MISSING, fields
from datetime import UTC, datetime

import pytest

from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionBinding,
    DecisionRejection,
    EventKind,
    HostAdapter,
    HostCapability,
    HostContractError,
    HostEvent,
)
from tests.fakes import FakeHostAdapter

NOW = datetime(2026, 9, 14, tzinfo=UTC)


def event(
    event_id: str,
    kind: EventKind,
    user_input_ref: str | None,
    action: DecisionAction | None,
    adapter_id: str = "codex",
    session_id: str = "session-1",
) -> HostEvent:
    return HostEvent(event_id, adapter_id, session_id, kind, NOW, user_input_ref, action)


def binding(adapter_id: str = "codex", session_id: str = "session-1") -> DecisionBinding:
    return DecisionBinding(
        "proposal-1",
        "create",
        adapter_id,
        session_id,
        "digest-1",
        (("knowledge-1", 1),),
        (DecisionAction.SAVE, DecisionAction.SKIP),
    )


def adapter() -> FakeHostAdapter:
    capability = HostCapability("user_input", True, "evidence/codex/user-input", "")
    return FakeHostAdapter("codex", "session-1", (capability,))


def test_required_dataclass_fields_have_no_defaults() -> None:
    for data_type in (HostCapability, HostEvent, DecisionBinding):
        assert all(field.default is MISSING for field in fields(data_type))
        assert all(field.default_factory is MISSING for field in fields(data_type))


def test_available_capability_requires_evidence() -> None:
    with pytest.raises(HostContractError, match="evidence_ref"):
        HostCapability("user_input", True, "", "")


def test_only_user_input_may_carry_decision_provenance() -> None:
    with pytest.raises(HostContractError, match="actual host provenance"):
        event("event-1", EventKind.USER_INPUT, None, DecisionAction.SAVE)
    with pytest.raises(HostContractError, match="non-user events"):
        event("event-2", EventKind.CHECKPOINT, "user-1", DecisionAction.SAVE)


def test_lifecycle_rejects_checkpoint_during_atomic_operation() -> None:
    host = adapter()
    assert isinstance(host, HostAdapter)
    host.on_session_start(event("event-1", EventKind.SESSION_START, None, None))
    host.on_atomic_begin(event("event-2", EventKind.ATOMIC_BEGIN, None, None))
    assert not host.checkpoint_eligible
    with pytest.raises(HostContractError, match="ineligible"):
        host.on_checkpoint(event("event-3", EventKind.CHECKPOINT, None, None))
    host.on_atomic_end(event("event-4", EventKind.ATOMIC_END, None, None))
    assert host.checkpoint_eligible


def test_lifecycle_rejects_invalid_order_and_identity() -> None:
    host = adapter()
    with pytest.raises(HostContractError, match="not started"):
        host.on_user_event(event("event-1", EventKind.USER_INPUT, "user-1", None))
    host.on_session_start(event("event-2", EventKind.SESSION_START, None, None))
    with pytest.raises(HostContractError, match="outside adapter session"):
        host.on_user_event(
            event(
                "event-3",
                EventKind.USER_INPUT,
                "user-2",
                None,
                session_id="another-session",
            )
        )
    with pytest.raises(HostContractError, match="not open"):
        host.on_atomic_end(event("event-4", EventKind.ATOMIC_END, None, None))


def test_decision_observation_requires_actual_matching_user_event_once() -> None:
    host = adapter()
    host.on_session_start(event("event-1", EventKind.SESSION_START, None, None))
    forged = event("event-2", EventKind.CHECKPOINT, None, None)
    assert host.register_decision_if_unambiguous(forged, binding()).rejection is (
        DecisionRejection.NOT_USER_INPUT
    )

    actual = event("event-3", EventKind.USER_INPUT, "host-user-event-3", DecisionAction.SAVE)
    host.on_user_event(actual)
    matched = host.register_decision_if_unambiguous(actual, binding())
    assert matched.matched
    assert matched.user_event_ref == "host-user-event-3"
    assert host.register_decision_if_unambiguous(actual, binding()).rejection is (
        DecisionRejection.ALREADY_OBSERVED
    )


@pytest.mark.parametrize(
    ("candidate_binding", "candidate_event", "expected"),
    [
        (
            binding(adapter_id="claude"),
            event("e1", EventKind.USER_INPUT, "u1", DecisionAction.SAVE),
            DecisionRejection.WRONG_ADAPTER,
        ),
        (
            binding(session_id="s2"),
            event("e2", EventKind.USER_INPUT, "u2", DecisionAction.SAVE),
            DecisionRejection.WRONG_SESSION,
        ),
        (
            binding(),
            event("e3", EventKind.USER_INPUT, "u3", DecisionAction.EDIT),
            DecisionRejection.ACTION_NOT_ALLOWED,
        ),
    ],
)
def test_decision_observation_rejects_mismatched_scope(
    candidate_binding: DecisionBinding,
    candidate_event: HostEvent,
    expected: DecisionRejection,
) -> None:
    host = adapter()
    host.on_session_start(event("start", EventKind.SESSION_START, None, None))
    observation = host.register_decision_if_unambiguous(candidate_event, candidate_binding)
    assert observation.rejection is expected


def test_session_end_prevents_decision_observation() -> None:
    host = adapter()
    host.on_session_start(event("event-1", EventKind.SESSION_START, None, None))
    host.on_session_end(event("event-2", EventKind.SESSION_END, None, None))
    actual = event("event-3", EventKind.USER_INPUT, "user-3", DecisionAction.SAVE)
    assert host.register_decision_if_unambiguous(actual, binding()).rejection is (
        DecisionRejection.SESSION_ENDED
    )
