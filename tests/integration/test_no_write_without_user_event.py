#!/usr/bin/env python3
# Purpose: Test HostAdapter rejection of forged, ambiguous, and incorrectly scoped approval.

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict, cast

import pytest

from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionBinding,
    EventKind,
    HostEvent,
)
from tests.fakes import FakeHostAdapter

pytestmark = pytest.mark.integration


class FixtureCase(TypedDict):
    case: str
    kind: str
    action: str | None
    adapter_id: str
    session_id: str
    expected_match: bool


def cases() -> list[FixtureCase]:
    path = Path(__file__).parents[1] / "fixtures" / "host_events.json"
    return cast(list[FixtureCase], json.loads(path.read_text(encoding="utf-8")))


@pytest.mark.parametrize("case", cases(), ids=lambda item: item["case"])
def test_only_actual_matching_user_event_can_match(case: FixtureCase) -> None:
    host = FakeHostAdapter("codex", "session-1", ())
    start = HostEvent(
        "start", "codex", "session-1", EventKind.SESSION_START, datetime.now(UTC), None, None
    )
    host.on_session_start(start)
    action = DecisionAction(case["action"]) if case["action"] is not None else None
    kind = EventKind(case["kind"])
    user_ref = f"actual:{case['case']}" if kind is EventKind.USER_INPUT else None
    event = HostEvent(
        case["case"],
        case["adapter_id"],
        case["session_id"],
        kind,
        datetime.now(UTC),
        user_ref,
        action,
    )
    binding = DecisionBinding(
        "proposal-1", "create", "codex", "session-1", "digest", (), (DecisionAction.SAVE,)
    )
    assert host.register_decision_if_unambiguous(event, binding).matched is case["expected_match"]
