#!/usr/bin/env python3
# Purpose: Verify deterministic Claude portions of AT-01, AT-03, AT-06, and AT-11.

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from expertiseos.hosts.claude_code import (
    ADAPTER_ID,
    ClaudeCapabilityEvidence,
    ClaudeCodeAdapter,
    ClaudeEnvironment,
    ClaudeRawEvent,
    EvidenceResult,
    InteractionKind,
    RawOrigin,
    interaction_allowed,
    plugin_commands,
)
from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionBinding,
    DecisionRejection,
    HostContractError,
)
from expertiseos.knowledge.backend import RetrievalResponse, SearchQuery
from expertiseos.learning.controls import (
    ContextScope,
    ControlReason,
    PeriodProgress,
    default_daily_settings,
    resolve_controls,
)

NOW = datetime(2026, 9, 14, 12, tzinfo=UTC)
ENVIRONMENT = ClaudeEnvironment("2.1.241", "macOS 15.1.1 build 24B91", "arm64", "default")
CONTEXT = ContextScope("terminal", "/workspace/project/main.py", "session-claude")


class _NoopService:
    def search(self, query: SearchQuery) -> RetrievalResponse:
        raise AssertionError("search is outside this acceptance fixture")

    def decline(self, proposal_id: str, fingerprint: str | None) -> object:
        return object()

    def expire_session(self, session_id: str) -> tuple[str, ...]:
        return ()

    def expire_unrelated_decisions(
        self, session_id: str, active_proposal_id: str | None
    ) -> tuple[str, ...]:
        return ()


def _evidence() -> tuple[ClaudeCapabilityEvidence, ...]:
    passed = "g0:claude-host-20260914:installed-interface"
    not_run = "g0:claude-host-20260914:not-run"
    return tuple(
        ClaudeCapabilityEvidence(
            ENVIRONMENT,
            name,
            (),
            passed if name in {"can_read", "can_search"} else not_run,
            EvidenceResult.PASS if name in {"can_read", "can_search"} else EvidenceResult.NOT_RUN,
            ""
            if name in {"can_read", "can_search"}
            else "authenticated live host fixture was not run",
        )
        for name in (
            "can_read",
            "can_search",
            "can_validate_user_decisions",
            "can_write",
            "can_observe_atomic_boundaries",
            "can_auto_activate",
        )
    )


def _adapter() -> ClaudeCodeAdapter:
    return ClaudeCodeAdapter("session-claude", ENVIRONMENT, _evidence(), _NoopService())


def _raw(
    event_id: str,
    event_name: str,
    origin: RawOrigin = RawOrigin.LIFECYCLE,
    prompt: str | None = None,
    user_input_ref: str | None = None,
) -> ClaudeRawEvent:
    return ClaudeRawEvent(
        event_id,
        event_name,
        "session-claude",
        NOW,
        origin,
        prompt,
        user_input_ref,
    )


def test_at01_reports_setup_commands_and_live_capability_limits() -> None:
    capabilities = {item.name: item for item in _adapter().capabilities()}

    assert capabilities["can_read"].available is True
    assert capabilities["can_search"].available is True
    assert all(
        capabilities[name].available is False
        for name in (
            "can_auto_activate",
            "can_observe_atomic_boundaries",
            "can_validate_user_decisions",
            "can_write",
        )
    )
    assert plugin_commands("./expertiseos", "expertiseos") == (
        ("claude", "plugin", "install", "./expertiseos"),
        ("claude", "plugin", "uninstall", "expertiseos"),
    )


def test_at03_atomic_sequence_defers_without_claiming_live_delivery() -> None:
    adapter = _adapter()
    adapter.handle_raw_event(_raw("start", "SessionStart"))
    adapter.handle_raw_event(_raw("begin", "PreToolUse", RawOrigin.TOOL))

    with pytest.raises(HostContractError, match="ineligible"):
        adapter.handle_raw_event(_raw("stop", "Stop"))

    adapter.handle_raw_event(_raw("end", "PostToolUse", RawOrigin.TOOL))
    active = resolve_controls(
        default_daily_settings("UTC", 1),
        PeriodProgress("2026-09-14", 0, Decimal("0"), (), ()),
        NOW,
    )
    assert adapter.comparison_due is True
    assert adapter.checkpoint_eligible(active, CONTEXT, (), InteractionKind.COLLECTION) is False


def test_at06_actual_save_event_still_cannot_authorize_an_unproven_write() -> None:
    adapter = _adapter()
    adapter.handle_raw_event(_raw("start", "SessionStart"))
    binding = DecisionBinding(
        "proposal-1",
        "create",
        ADAPTER_ID,
        "session-claude",
        "digest-1",
        (),
        (DecisionAction.SAVE,),
    )
    adapter.set_active_binding(binding)
    event = adapter.handle_raw_event(
        _raw("save", "UserPromptSubmit", RawOrigin.USER, "Save", "claude:save")
    )
    observation = adapter.register_decision_if_unambiguous(event, binding)

    assert event.action is DecisionAction.SAVE
    assert observation.matched is False
    assert observation.rejection is DecisionRejection.ACTION_NOT_ALLOWED
    assert adapter.write_capable is False


def test_at11_pause_preserves_recall_without_resuming_collection() -> None:
    settings = dataclasses.replace(default_daily_settings("UTC", 1), learning_paused=True)
    progress = PeriodProgress("2026-09-14", 0, Decimal("0"), (), ())
    resolution = resolve_controls(settings, progress, NOW)

    assert resolution.reason is ControlReason.PAUSED
    assert interaction_allowed(resolution, CONTEXT, (), InteractionKind.RECALL) is True
    assert interaction_allowed(resolution, CONTEXT, (), InteractionKind.OBSERVE) is False
    assert interaction_allowed(resolution, CONTEXT, (), InteractionKind.COLLECTION) is False
    assert interaction_allowed(resolution, CONTEXT, (), InteractionKind.EXERCISE) is False
