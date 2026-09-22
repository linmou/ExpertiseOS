#!/usr/bin/env python3
# Purpose: Verify the C004 control-resolution handoff into the C006 Claude adapter.

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from expertiseos.hosts.claude_code import (
    ClaudeCapabilityEvidence,
    ClaudeCodeAdapter,
    ClaudeEnvironment,
    ClaudeRawEvent,
    EvidenceResult,
    InteractionKind,
    RawOrigin,
    interaction_allowed,
)
from expertiseos.hosts.contract import HostContractError
from expertiseos.knowledge.backend import (
    IndexState,
    RetrievalResponse,
    SearchMode,
    SearchQuery,
    StoreState,
)
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
ENVIRONMENT = ClaudeEnvironment("2.1.241", "macOS 15.1.1 build 24B91", "arm64", "default")
CONTEXT = ContextScope("terminal", "/workspace/project/main.py", "session-claude")


class _RecordingService:
    def __init__(self) -> None:
        self.search_count = 0

    def search(self, query: SearchQuery) -> RetrievalResponse:
        self.search_count += 1
        return RetrievalResponse(
            (),
            SearchMode.LOCAL_INDEXED,
            False,
            StoreState.READY,
            IndexState.READY,
            True,
        )

    def decline(self, proposal_id: str, fingerprint: str | None) -> object:
        return object()

    def expire_session(self, session_id: str) -> tuple[str, ...]:
        return ()

    def expire_unrelated_decisions(
        self, session_id: str, active_proposal_id: str | None
    ) -> tuple[str, ...]:
        return ()


def _evidence() -> tuple[ClaudeCapabilityEvidence, ...]:
    return (
        ClaudeCapabilityEvidence(
            ENVIRONMENT,
            "can_read",
            (),
            "g0:claude-host-20260914:installed-interface",
            EvidenceResult.PASS,
            "live plugin activation is not proven",
        ),
        ClaudeCapabilityEvidence(
            ENVIRONMENT,
            "can_search",
            (),
            "g0:claude-host-20260914:installed-interface",
            EvidenceResult.PASS,
            "live plugin activation is not proven",
        ),
        *tuple(
            ClaudeCapabilityEvidence(
                ENVIRONMENT,
                name,
                (),
                "g0:claude-host-20260914:not-run",
                EvidenceResult.NOT_RUN,
                "authenticated live host fixture was not run",
            )
            for name in (
                "can_validate_user_decisions",
                "can_write",
                "can_observe_atomic_boundaries",
                "can_auto_activate",
            )
        ),
    )


def _adapter(service: _RecordingService | None = None) -> ClaudeCodeAdapter:
    selected_service = _RecordingService() if service is None else service
    return ClaudeCodeAdapter("session-claude", ENVIRONMENT, _evidence(), selected_service)


def _progress(reflection_count: int = 0) -> PeriodProgress:
    return PeriodProgress("2026-09-14", reflection_count, Decimal("0"), (), ())


@pytest.mark.parametrize(
    ("reason", "reflection_count", "expected"),
    [
        (ControlReason.ACTIVE, 0, (True, True, True, True)),
        (ControlReason.PAUSED, 0, (False, False, False, True)),
        (ControlReason.FATIGUE_REST, 0, (False, False, False, True)),
        (ControlReason.TARGET_SATISFIED, 1, (True, True, False, True)),
        (ControlReason.DISABLED, 0, (False, False, False, False)),
    ],
)
def test_actual_control_resolutions_gate_every_claude_interaction(
    reason: ControlReason,
    reflection_count: int,
    expected: tuple[bool, bool, bool, bool],
) -> None:
    settings = default_daily_settings("UTC", 1)
    if reason is ControlReason.PAUSED:
        settings = dataclasses.replace(settings, learning_paused=True)
    elif reason is ControlReason.FATIGUE_REST:
        settings = dataclasses.replace(settings, fatigue_rest_until=NOW + timedelta(hours=1))
    elif reason is ControlReason.DISABLED:
        settings = dataclasses.replace(settings, enabled=False)
    resolution = resolve_controls(settings, _progress(reflection_count), NOW)

    assert resolution.reason is reason
    assert (
        tuple(
            interaction_allowed(resolution, CONTEXT, (), interaction)
            for interaction in InteractionKind
        )
        == expected
    )


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        (ExclusionKind.SOURCE, "terminal"),
        (ExclusionKind.PATH, "/workspace/project"),
        (ExclusionKind.SESSION, "session-claude"),
    ],
)
def test_scope_exclusions_block_every_claude_interaction(kind: ExclusionKind, value: str) -> None:
    resolution = resolve_controls(default_daily_settings("UTC", 1), _progress(), NOW)
    exclusion = ScopeExclusion("exclusion-1", kind, value, NOW, "receipt-1")

    assert all(
        not interaction_allowed(resolution, CONTEXT, (exclusion,), interaction)
        for interaction in InteractionKind
    )


def test_pause_resolution_reaches_real_claude_retrieval_guard() -> None:
    service = _RecordingService()
    adapter = _adapter(service)
    settings = dataclasses.replace(default_daily_settings("UTC", 1), learning_paused=True)
    resolution = resolve_controls(settings, _progress(), NOW)
    response = adapter.search(
        SearchQuery("approved topic", 3, None, (), (), ()), resolution, CONTEXT, ()
    )

    assert response is not None
    assert service.search_count == 1
    assert interaction_allowed(resolution, CONTEXT, (), InteractionKind.OBSERVE) is False


def test_normalized_atomic_sequence_cannot_claim_an_unproven_safe_checkpoint() -> None:
    adapter = _adapter()
    adapter.handle_raw_event(
        ClaudeRawEvent(
            "start",
            "SessionStart",
            "session-claude",
            NOW,
            RawOrigin.LIFECYCLE,
            None,
            None,
        )
    )
    adapter.handle_raw_event(
        ClaudeRawEvent(
            "begin",
            "PreToolUse",
            "session-claude",
            NOW,
            RawOrigin.TOOL,
            None,
            None,
        )
    )
    active = resolve_controls(default_daily_settings("UTC", 1), _progress(), NOW)

    with pytest.raises(HostContractError, match="ineligible"):
        adapter.handle_raw_event(
            ClaudeRawEvent(
                "stop",
                "Stop",
                "session-claude",
                NOW,
                RawOrigin.LIFECYCLE,
                None,
                None,
            )
        )
    adapter.handle_raw_event(
        ClaudeRawEvent(
            "end",
            "PostToolUse",
            "session-claude",
            NOW,
            RawOrigin.TOOL,
            None,
            None,
        )
    )

    assert adapter.comparison_due is True
    assert adapter.checkpoint_eligible(active, CONTEXT, (), InteractionKind.COLLECTION) is False
    assert adapter.capability_available("can_observe_atomic_boundaries") is False
