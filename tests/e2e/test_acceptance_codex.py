#!/usr/bin/env python3
# Purpose: Verify deterministic Codex portions of AT-01, AT-03, AT-06, and AT-11.

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from expertiseos.approval.gate import DecisionGrantStore
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.hosts.codex import (
    CodexAdapter,
    CodexEnvironment,
    normalize_hook,
    registration_plan,
    should_observe,
    should_retrieve,
)
from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionBinding,
    DecisionRejection,
    HostContractError,
)
from expertiseos.learning.controls import (
    ContextScope,
    ControlReason,
    PeriodProgress,
    default_daily_settings,
    resolve_controls,
)

NOW = datetime(2026, 9, 14, 12, tzinfo=UTC)


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


def _hook(name: str, **values: object) -> dict[str, object]:
    return {"hook_event_name": name, "session_id": "session-codex", **values}


def test_at01_reports_static_setup_and_live_capability_limits() -> None:
    capabilities = {item.name: item for item in _adapter().capabilities()}
    plan = registration_plan("expertiseos", "local-marketplace")

    assert capabilities["can_read"].available is True
    assert capabilities["can_search"].available is True
    for name in (
        "can_auto_activate",
        "can_observe_atomic_boundaries",
        "can_validate_user_decisions",
        "can_write",
    ):
        assert capabilities[name].available is False
        assert capabilities[name].limitation == "live authenticated host fixture not run"
    assert plan.install_command == (
        "codex",
        "plugin",
        "add",
        "expertiseos@local-marketplace",
        "--json",
    )
    assert plan.remove_command == (
        "codex",
        "plugin",
        "remove",
        "expertiseos@local-marketplace",
        "--json",
    )
    assert plan.preserves_unrelated_configuration is False
    assert plan.live_verified is False


def test_at03_atomic_sequence_is_not_interrupted_or_promoted_as_live_safe() -> None:
    adapter = _adapter()
    adapter.on_session_start(normalize_hook(_hook("SessionStart", event_id="start"), NOW))
    adapter.on_atomic_begin(normalize_hook(_hook("PreToolUse", tool_use_id="tool"), NOW))
    adapter.mark_comparison_due()

    with pytest.raises(HostContractError, match="ineligible"):
        adapter.on_checkpoint(normalize_hook(_hook("Stop", event_id="stop"), NOW))

    adapter.on_atomic_end(normalize_hook(_hook("PostToolUse", tool_use_id="tool"), NOW))
    adapter.on_checkpoint(normalize_hook(_hook("Stop", event_id="stop"), NOW))

    assert adapter.comparison_ready is False
    assert adapter.consume_comparison_due() is False


def test_at06_prompt_text_cannot_become_an_authenticated_write_decision() -> None:
    adapter = _adapter()
    adapter.on_session_start(normalize_hook(_hook("SessionStart", event_id="start"), NOW))
    user_event = normalize_hook(_hook("UserPromptSubmit", turn_id="turn-save", prompt="Save"), NOW)
    adapter.on_user_event(user_event)
    observation = adapter.register_decision_if_unambiguous(
        user_event,
        DecisionBinding(
            "proposal-1",
            "create",
            "codex",
            "session-codex",
            "digest-1",
            (),
            (DecisionAction.SAVE,),
        ),
    )

    assert user_event.action is None
    assert observation.matched is False
    assert observation.rejection is DecisionRejection.AMBIGUOUS_ACTION
    assert {item.name: item.available for item in adapter.capabilities()}["can_write"] is False


def test_at11_pause_preserves_approved_recall_without_resuming_collection() -> None:
    settings = dataclasses.replace(default_daily_settings("UTC", 1), learning_paused=True)
    progress = PeriodProgress("2026-09-14", 0, Decimal("0"), (), ())
    resolution = resolve_controls(settings, progress, NOW)
    context = ContextScope("terminal", "/workspace/project/main.py", "session-codex")
    capabilities = _adapter().capabilities()

    assert resolution.reason is ControlReason.PAUSED
    assert should_observe(resolution, context, (), capabilities) is False
    assert should_retrieve(resolution, context, (), capabilities) is True
    assert resolution.prompt_collection is False
    assert resolution.proactive_exercises is False
