#!/usr/bin/env python3
# Purpose: Test src/expertiseos/hosts/codex.py conservative atomic checkpoint handling.

from datetime import UTC, datetime

import pytest

from expertiseos.approval.gate import DecisionGrantStore
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.hosts.codex import CodexAdapter, CodexEnvironment
from expertiseos.hosts.contract import EventKind, HostContractError, HostEvent

NOW = datetime(2026, 9, 14, tzinfo=UTC)


def event(identifier: str, kind: EventKind) -> HostEvent:
    return HostEvent(identifier, "codex", "session-1", kind, NOW, None, None)


def started_adapter() -> CodexAdapter:
    host = CodexAdapter(
        CodexEnvironment("0.146.1", "macOS 15.1.1 build 24B91", "arm64", "workspace-write"),
        "session-1",
        CandidateStore(),
        DecisionGrantStore(),
    )
    host.on_session_start(event("start", EventKind.SESSION_START))
    return host


def test_nested_atomic_sequence_rejects_early_checkpoint() -> None:
    host = started_adapter()
    host.on_atomic_begin(event("begin-1", EventKind.ATOMIC_BEGIN))
    host.on_atomic_begin(event("begin-2", EventKind.ATOMIC_BEGIN))
    host.mark_comparison_due()
    with pytest.raises(HostContractError, match="ineligible"):
        host.on_checkpoint(event("early", EventKind.CHECKPOINT))
    host.on_atomic_end(event("end-2", EventKind.ATOMIC_END))
    host.on_atomic_end(event("end-1", EventKind.ATOMIC_END))
    host.on_checkpoint(event("safe-shape", EventKind.CHECKPOINT))
    assert host.comparison_ready is False
    assert host.consume_comparison_due() is False


def test_unbalanced_atomic_event_fails_closed() -> None:
    host = started_adapter()
    with pytest.raises(HostContractError, match="not open"):
        host.on_atomic_end(event("unexpected-end", EventKind.ATOMIC_END))
    with pytest.raises(HostContractError, match="unknown or open"):
        host.on_checkpoint(event("checkpoint", EventKind.CHECKPOINT))


def test_comparison_due_coalesces_without_claiming_unverified_checkpoint() -> None:
    host = started_adapter()
    host.mark_comparison_due()
    host.mark_comparison_due()
    assert not host.checkpoint_eligible
    assert not host.consume_comparison_due()
