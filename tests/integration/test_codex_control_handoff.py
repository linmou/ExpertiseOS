#!/usr/bin/env python3
# Purpose: Verify the C004 control-resolution handoff into the C005 Codex adapter.

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from expertiseos.approval.gate import DecisionGrantStore
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.hosts.codex import (
    CodexAdapter,
    CodexEnvironment,
    normalize_hook,
    should_observe,
    should_retrieve,
)
from expertiseos.hosts.contract import EventKind, HostContractError
from expertiseos.learning.controls import (
    ContextScope,
    ControlReason,
    ExclusionKind,
    PeriodProgress,
    ScopeExclusion,
    default_daily_settings,
    resolve_controls,
)

NOW = datetime(2026, 9, 14, 12, tzinfo=UTC)
CONTEXT = ContextScope("terminal", "/workspace/project/main.py", "session-codex")


def _progress(reflection_count: int = 0) -> PeriodProgress:
    return PeriodProgress("2026-09-14", reflection_count, Decimal("0"), (), ())


def _adapter() -> CodexAdapter:
    return CodexAdapter(
        CodexEnvironment(
            "0.146.1",
            "macOS 15.1.1 build 24B91",
            "arm64",
            "workspace-write",
        ),
        "session-codex",
        CandidateStore(),
        DecisionGrantStore(),
    )


@pytest.mark.parametrize(
    ("reason", "reflection_count", "observe", "retrieve"),
    [
        (ControlReason.ACTIVE, 0, True, True),
        (ControlReason.PAUSED, 0, False, True),
        (ControlReason.FATIGUE_REST, 0, False, True),
        (ControlReason.TARGET_SATISFIED, 1, True, True),
        (ControlReason.DISABLED, 0, False, False),
    ],
)
def test_actual_control_resolutions_gate_codex_paths(
    reason: ControlReason,
    reflection_count: int,
    observe: bool,
    retrieve: bool,
) -> None:
    settings = default_daily_settings("UTC", 1)
    if reason is ControlReason.PAUSED:
        settings = dataclasses.replace(settings, learning_paused=True)
    elif reason is ControlReason.FATIGUE_REST:
        settings = dataclasses.replace(settings, fatigue_rest_until=NOW + timedelta(hours=1))
    elif reason is ControlReason.DISABLED:
        settings = dataclasses.replace(settings, enabled=False)
    resolution = resolve_controls(settings, _progress(reflection_count), NOW)
    capabilities = _adapter().capabilities()

    assert resolution.reason is reason
    assert resolution.observe is observe
    assert resolution.approved_recall is retrieve
    assert should_observe(resolution, CONTEXT, (), capabilities) is False
    assert should_retrieve(resolution, CONTEXT, (), capabilities) is retrieve
    assert {item.name: item.available for item in capabilities}["can_write"] is False


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        (ExclusionKind.SOURCE, "terminal"),
        (ExclusionKind.PATH, "/workspace/project"),
        (ExclusionKind.SESSION, "session-codex"),
    ],
)
def test_scope_exclusions_block_codex_observation_and_retrieval(
    kind: ExclusionKind, value: str
) -> None:
    resolution = resolve_controls(default_daily_settings("UTC", 1), _progress(), NOW)
    exclusion = ScopeExclusion("exclusion-1", kind, value, NOW, "receipt-1")
    capabilities = _adapter().capabilities()

    assert should_observe(resolution, CONTEXT, (exclusion,), capabilities) is False
    assert should_retrieve(resolution, CONTEXT, (exclusion,), capabilities) is False


def test_normalized_atomic_events_defer_comparison_without_live_boundary_evidence() -> None:
    adapter = _adapter()
    start = normalize_hook(
        {
            "hook_event_name": "SessionStart",
            "session_id": "session-codex",
            "event_id": "start-1",
        },
        NOW,
    )
    begin = normalize_hook(
        {
            "hook_event_name": "PreToolUse",
            "session_id": "session-codex",
            "tool_use_id": "tool-1",
        },
        NOW,
    )
    end = normalize_hook(
        {
            "hook_event_name": "PostToolUse",
            "session_id": "session-codex",
            "tool_use_id": "tool-1",
        },
        NOW,
    )
    checkpoint = normalize_hook(
        {
            "hook_event_name": "Stop",
            "session_id": "session-codex",
            "event_id": "stop-1",
        },
        NOW,
    )

    adapter.on_session_start(start)
    adapter.on_atomic_begin(begin)
    adapter.mark_comparison_due()
    with pytest.raises(HostContractError, match="ineligible"):
        adapter.on_checkpoint(checkpoint)

    adapter.on_atomic_end(end)
    adapter.on_checkpoint(checkpoint)

    assert tuple(event.kind for event in adapter.events) == (
        EventKind.SESSION_START,
        EventKind.ATOMIC_BEGIN,
        EventKind.ATOMIC_END,
        EventKind.CHECKPOINT,
    )
    assert adapter.checkpoint_eligible is False
    assert adapter.comparison_ready is False
    assert adapter.consume_comparison_due() is False
    assert {item.name: item.available for item in adapter.capabilities()}[
        "can_observe_atomic_boundaries"
    ] is False
