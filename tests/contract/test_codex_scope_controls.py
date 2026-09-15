#!/usr/bin/env python3
# Purpose: Test src/expertiseos/hosts/codex.py consumption of C004 controls and exclusions.

from datetime import UTC, datetime

from expertiseos.hosts.codex import (
    CodexEnvironment,
    capabilities_for,
    should_observe,
    should_retrieve,
)
from expertiseos.learning.controls import (
    ContextScope,
    ControlReason,
    ControlResolution,
    ExclusionKind,
    ScopeExclusion,
)

NOW = datetime(2026, 9, 14, tzinfo=UTC)
CAPABILITIES = capabilities_for(
    CodexEnvironment("0.146.1", "macOS 15.1.1 build 24B91", "arm64", "workspace-write")
)
ACTIVE = ControlResolution(ControlReason.ACTIVE, True, True, True, True, None)


def exclusion(kind: ExclusionKind, value: str) -> ScopeExclusion:
    return ScopeExclusion("exclude-1", kind, value, NOW, "receipt-1")


def test_read_only_profile_never_forwards_observation() -> None:
    context = ContextScope(None, "/repo/a.py", "session-1")
    assert not should_observe(ACTIVE, context, (), CAPABILITIES)


def test_approved_recall_consumes_control_resolution() -> None:
    context = ContextScope(None, "/repo/a.py", "session-1")
    assert should_retrieve(ACTIVE, context, (), CAPABILITIES)
    disabled = ControlResolution(ControlReason.DISABLED, False, False, False, False, None)
    assert not should_retrieve(disabled, context, (), CAPABILITIES)


def test_source_path_and_session_exclusions_block_retrieval() -> None:
    cases = (
        (ContextScope("source-1", None, None), exclusion(ExclusionKind.SOURCE, "source-1")),
        (
            ContextScope(None, "/repo/private/a.py", None),
            exclusion(ExclusionKind.PATH, "/repo/private"),
        ),
        (ContextScope(None, None, "session-1"), exclusion(ExclusionKind.SESSION, "session-1")),
    )
    for context, item in cases:
        assert not should_retrieve(ACTIVE, context, (item,), CAPABILITIES)
