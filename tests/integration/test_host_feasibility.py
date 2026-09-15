#!/usr/bin/env python3
# Purpose: Test HostAdapter contract feasibility for an exact actual-user decision sequence.

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

import pytest

from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionBinding,
    DecisionRejection,
    EventKind,
    HostCapability,
    HostContractError,
    HostEvent,
)
from expertiseos.knowledge.backend import ApprovedKnowledgeInput, IndexState, SearchMode, StoreState
from tests.fakes import (
    DeterministicClock,
    DeterministicIdGenerator,
    FakeHostAdapter,
    FakeKnowledgeBackend,
)

pytestmark = pytest.mark.integration
NOW = datetime(2026, 9, 14, tzinfo=UTC)


def host_event(
    event_id: str,
    kind: EventKind,
    user_input_ref: str | None,
    action: DecisionAction | None,
) -> HostEvent:
    return HostEvent(event_id, "host", "session-1", kind, NOW, user_input_ref, action)


def test_six_step_actual_user_decision_fixture() -> None:
    capability = HostCapability("actual_user_input", True, "fixture:user-input", "")
    host = FakeHostAdapter("host", "session-1", (capability,))
    clock = DeterministicClock(NOW, timedelta(seconds=1))
    backend = FakeKnowledgeBackend(
        clock,
        DeterministicIdGenerator("knowledge", 1),
        StoreState.READY,
        IndexState.READY,
        SearchMode.KEYWORD,
    )
    content = "Retry only when the operation is known to be idempotent."
    value = ApprovedKnowledgeInput(
        content,
        hashlib.sha256(content.encode()).hexdigest(),
        ("procedure",),
        ("domain",),
        None,
        "observed",
        ("host-user-2",),
        "user",
    )
    binding = DecisionBinding(
        "proposal-1",
        "create",
        "host",
        "session-1",
        value.content_digest,
        (),
        (DecisionAction.SAVE,),
    )

    host.on_session_start(host_event("start", EventKind.SESSION_START, None, None))
    forged = host_event("forged", EventKind.CHECKPOINT, None, None)
    assert host.register_decision_if_unambiguous(forged, binding).rejection is (
        DecisionRejection.NOT_USER_INPUT
    )
    assert backend.get_current_versions(()) == {}

    user_save = host_event("user-2", EventKind.USER_INPUT, "host-user-2", DecisionAction.SAVE)
    host.on_user_event(user_save)
    observation = host.register_decision_if_unambiguous(user_save, binding)
    assert observation.matched
    saved = backend.create_approved(value, "operation-1")
    assert backend.create_approved(value, "operation-1") == saved
    assert host.register_decision_if_unambiguous(user_save, binding).rejection is (
        DecisionRejection.ALREADY_OBSERVED
    )


def test_atomic_sequence_defers_checkpoint_until_end() -> None:
    host = FakeHostAdapter("host", "session-1", ())
    host.on_session_start(host_event("start", EventKind.SESSION_START, None, None))
    host.on_atomic_begin(host_event("begin", EventKind.ATOMIC_BEGIN, None, None))
    with pytest.raises(HostContractError, match="ineligible"):
        host.on_checkpoint(host_event("checkpoint-early", EventKind.CHECKPOINT, None, None))
    host.on_atomic_end(host_event("end", EventKind.ATOMIC_END, None, None))
    host.on_checkpoint(host_event("checkpoint-safe", EventKind.CHECKPOINT, None, None))
    assert host.events[-1].event_id == "checkpoint-safe"
