#!/usr/bin/env python3
# Purpose: Test src/expertiseos/hosts/codex.py blocks unverified Codex write decisions.

from datetime import UTC, datetime

import pytest

from expertiseos.approval.gate import DecisionGrantStore
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.hosts.codex import CodexAdapter, CodexEnvironment
from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionBinding,
    DecisionObservation,
    DecisionRejection,
    EventKind,
    HostContractError,
    HostEvent,
)

NOW = datetime(2026, 9, 14, tzinfo=UTC)
DIGEST = "a" * 64


def adapter() -> CodexAdapter:
    return CodexAdapter(
        CodexEnvironment("0.146.1", "macOS 15.1.1 build 24B91", "arm64", "workspace-write"),
        "session-1",
        CandidateStore(),
        DecisionGrantStore(),
    )


def binding(adapter_id: str = "codex", session_id: str = "session-1") -> DecisionBinding:
    return DecisionBinding(
        "proposal-1",
        "create",
        adapter_id,
        session_id,
        DIGEST,
        (),
        (DecisionAction.SAVE, DecisionAction.EDIT, DecisionAction.SKIP),
    )


def user_event(
    action: DecisionAction | None,
    adapter_id: str = "codex",
    session_id: str = "session-1",
) -> HostEvent:
    return HostEvent("user-1", adapter_id, session_id, EventKind.USER_INPUT, NOW, "turn-1", action)


@pytest.mark.parametrize("action", list(DecisionAction))
def test_static_user_schema_cannot_authorize_any_action(action: DecisionAction) -> None:
    result = adapter().register_decision_if_unambiguous(user_event(action), binding())
    expected = (
        DecisionRejection.MISSING_USER_PROVENANCE
        if action in binding().allowed_actions
        else DecisionRejection.ACTION_NOT_ALLOWED
    )
    assert result == DecisionObservation(False, None, None, expected)


def test_model_tool_and_checkpoint_events_are_not_user_input() -> None:
    event = HostEvent("tool-1", "codex", "session-1", EventKind.CHECKPOINT, NOW, None, None)
    result = adapter().register_decision_if_unambiguous(event, binding())
    assert result.rejection is DecisionRejection.NOT_USER_INPUT


def test_ambiguous_wrong_host_and_wrong_session_are_rejected() -> None:
    host = adapter()
    assert host.register_decision_if_unambiguous(user_event(None), binding()).rejection is (
        DecisionRejection.AMBIGUOUS_ACTION
    )
    assert (
        host.register_decision_if_unambiguous(
            user_event(DecisionAction.SAVE, adapter_id="claude-code"), binding()
        ).rejection
        is DecisionRejection.WRONG_ADAPTER
    )
    assert (
        host.register_decision_if_unambiguous(
            user_event(DecisionAction.SAVE, session_id="session-2"), binding()
        ).rejection
        is DecisionRejection.WRONG_SESSION
    )


def test_multiple_active_proposals_require_external_disambiguation() -> None:
    host = adapter()
    host.on_session_start(
        HostEvent("start", "codex", "session-1", EventKind.SESSION_START, NOW, None, None)
    )
    host.display_proposal(binding())
    second = DecisionBinding(
        "proposal-2",
        "create",
        "codex",
        "session-1",
        "b" * 64,
        (),
        (DecisionAction.SAVE,),
    )
    with pytest.raises(HostContractError, match="multiple active proposals"):
        host.display_proposal(second)
