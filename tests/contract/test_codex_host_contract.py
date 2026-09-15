#!/usr/bin/env python3
# Purpose: Test src/expertiseos/hosts/codex.py hook normalization and session identity.

from datetime import UTC, datetime

import pytest

from expertiseos.approval.gate import DecisionGrantStore
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.hosts.codex import CodexAdapter, CodexEnvironment, normalize_hook
from expertiseos.hosts.contract import EventKind, HostContractError

NOW = datetime(2026, 9, 14, tzinfo=UTC)


def adapter() -> CodexAdapter:
    return CodexAdapter(
        CodexEnvironment("0.146.1", "macOS 15.1.1 build 24B91", "arm64", "workspace-write"),
        "session-1",
        CandidateStore(),
        DecisionGrantStore(),
    )


def payload(name: str, **values: object) -> dict[str, object]:
    return {"hook_event_name": name, "session_id": "session-1", **values}


def test_normalizes_public_hook_shapes_without_prompt_text() -> None:
    start = normalize_hook(payload("SessionStart", event_id="start"), NOW)
    user = normalize_hook(payload("UserPromptSubmit", turn_id="turn-1", prompt="Save"), NOW)
    begin = normalize_hook(payload("PreToolUse", tool_use_id="tool-1"), NOW)
    end = normalize_hook(payload("PostToolUseFailure", tool_use_id="tool-1"), NOW)
    stop = normalize_hook(payload("Stop", event_id="stop"), NOW)

    assert [item.kind for item in (start, user, begin, end, stop)] == [
        EventKind.SESSION_START,
        EventKind.USER_INPUT,
        EventKind.ATOMIC_BEGIN,
        EventKind.ATOMIC_END,
        EventKind.CHECKPOINT,
    ]
    assert user.user_input_ref == "turn-1"
    assert user.action is None
    assert "Save" not in repr(user)


@pytest.mark.parametrize(
    "value, message",
    [
        ({"session_id": "session-1", "event_id": "x"}, "hook_event_name"),
        (payload("Unknown", event_id="x"), "unsupported Codex hook"),
        (payload("UserPromptSubmit", turn_id="turn-1"), "prompt"),
        (payload("SessionStart"), "event_id"),
    ],
)
def test_rejects_incomplete_or_unknown_payloads(value: dict[str, object], message: str) -> None:
    with pytest.raises(HostContractError, match=message):
        normalize_hook(value, NOW)


def test_rejects_naive_timestamps_and_wrong_session_events() -> None:
    with pytest.raises(HostContractError, match="timezone-aware"):
        normalize_hook(payload("SessionStart", event_id="start"), datetime(2026, 9, 14))

    host = adapter()
    wrong = normalize_hook(
        {"hook_event_name": "SessionStart", "session_id": "other", "event_id": "start"},
        NOW,
    )
    with pytest.raises(HostContractError, match="outside Codex adapter session"):
        host.on_session_start(wrong)


def test_lifecycle_rejects_duplicate_and_prestart_events() -> None:
    host = adapter()
    user = normalize_hook(payload("UserPromptSubmit", turn_id="turn-1", prompt="hello"), NOW)
    with pytest.raises(HostContractError, match="has not started"):
        host.on_user_event(user)

    start = normalize_hook(payload("SessionStart", event_id="start"), NOW)
    host.on_session_start(start)
    with pytest.raises(HostContractError, match="duplicate host event"):
        host.on_session_start(start)
