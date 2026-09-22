#!/usr/bin/env python3
# Purpose: Test C001 host/backend outputs consumed through the integration bootstrap boundary.

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

import pytest

from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionBinding,
    DecisionObservation,
    EventKind,
    HostEvent,
)
from expertiseos.knowledge.backend import (
    ApprovedKnowledgeInput,
    IndexState,
    KnowledgeRecord,
    SearchMode,
    StoreState,
)
from tests.fakes import (
    DeterministicClock,
    DeterministicIdGenerator,
    FakeHostAdapter,
    FakeKnowledgeBackend,
)

pytestmark = pytest.mark.integration


def consume_foundation_handoff(
    observation: DecisionObservation, record: KnowledgeRecord
) -> tuple[str, str, int]:
    """Represent the narrow contract facts available to the next component."""
    if not observation.matched or observation.user_event_ref is None:
        raise ValueError("bootstrap consumer requires an actual matched user event")
    return observation.user_event_ref, record.id, record.version


def test_actual_c001_outputs_reach_bootstrap_consumer() -> None:
    now = datetime(2026, 9, 14, tzinfo=UTC)
    host = FakeHostAdapter("codex", "session-1", ())
    host.on_session_start(
        HostEvent("start-1", "codex", "session-1", EventKind.SESSION_START, now, None, None)
    )
    user_event = HostEvent(
        "event-1",
        "codex",
        "session-1",
        EventKind.USER_INPUT,
        now,
        "host-user-event-1",
        DecisionAction.SAVE,
    )
    host.on_user_event(user_event)
    binding = DecisionBinding(
        "proposal-1",
        "create",
        "codex",
        "session-1",
        "digest-1",
        (),
        (DecisionAction.SAVE,),
    )
    observation = host.register_decision_if_unambiguous(user_event, binding)

    backend = FakeKnowledgeBackend(
        DeterministicClock(now, timedelta(seconds=1)),
        DeterministicIdGenerator("knowledge", 1),
        StoreState.READY,
        IndexState.READY,
        SearchMode.KEYWORD,
    )
    content = "approved bootstrap evidence"
    approved = ApprovedKnowledgeInput(
        content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
        ("procedure",),
        ("bootstrap",),
        None,
        "observed",
        ("host-user-event-1",),
        "user",
    )
    record = backend.create_approved(approved, "operation-1")

    assert consume_foundation_handoff(observation, record) == (
        "host-user-event-1",
        "knowledge-1",
        1,
    )
