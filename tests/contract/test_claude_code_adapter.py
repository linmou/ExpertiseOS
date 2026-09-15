#!/usr/bin/env python3
# Purpose: Test src/expertiseos/hosts/claude_code.py translation and fail-closed boundaries.

from __future__ import annotations

import json
from dataclasses import MISSING, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest

from expertiseos.domain.models import CommitResult, CommitStatus
from expertiseos.hosts.claude_code import (
    ADAPTER_ID,
    ClaudeCapabilityEvidence,
    ClaudeCodeAdapter,
    ClaudeEnvironment,
    ClaudeRawEvent,
    EvidenceResult,
    InteractionKind,
    RawOrigin,
    capabilities_for,
    direct_save_content,
    explicit_edit_content,
    interaction_allowed,
    is_saved_result,
    parse_explicit_action,
    plugin_commands,
)
from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionBinding,
    DecisionRejection,
    EventKind,
    HostAdapter,
    HostContractError,
)
from expertiseos.knowledge.backend import SearchQuery
from expertiseos.learning.controls import (
    ContextScope,
    ControlReason,
    ControlResolution,
    ExclusionKind,
    ScopeExclusion,
)

NOW = datetime(2026, 9, 14, tzinfo=UTC)
FIXTURE = Path(__file__).parents[1] / "fixtures" / "claude_code" / "g0_events.json"


class RecordingService:
    def __init__(self, fail: bool) -> None:
        self.fail = fail
        self.expired_sessions: list[str] = []
        self.declined: list[str] = []
        self.unrelated: list[tuple[str, str | None]] = []

    def search(self, query: object) -> Any:
        if self.fail:
            raise ConnectionError("service unavailable")
        return query

    def decline(self, proposal_id: str, fingerprint: str | None) -> object:
        if self.fail:
            raise ConnectionError("service unavailable")
        self.declined.append(proposal_id)
        return object()

    def expire_session(self, session_id: str) -> tuple[str, ...]:
        if self.fail:
            raise ConnectionError("service unavailable")
        self.expired_sessions.append(session_id)
        return ()

    def expire_unrelated_decisions(
        self, session_id: str, active_proposal_id: str | None
    ) -> tuple[str, ...]:
        if self.fail:
            raise ConnectionError("service unavailable")
        self.unrelated.append((session_id, active_proposal_id))
        return ()


def fixture_data() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(FIXTURE.read_text(encoding="utf-8")))


def environment() -> ClaudeEnvironment:
    value = fixture_data()["environment"]
    return ClaudeEnvironment(
        value["version"],
        value["operating_system"],
        value["architecture"],
        value["permission_mode"],
    )


def evidence() -> tuple[ClaudeCapabilityEvidence, ...]:
    env = environment()
    return tuple(
        ClaudeCapabilityEvidence(
            env,
            item["name"],
            (),
            item["evidence_ref"],
            EvidenceResult(item["result"]),
            item["limitation"],
        )
        for item in fixture_data()["capabilities"]
    )


def adapter(
    service: RecordingService | None = None,
    selected_evidence: tuple[ClaudeCapabilityEvidence, ...] | None = None,
) -> ClaudeCodeAdapter:
    return ClaudeCodeAdapter(
        "session-1",
        environment(),
        evidence() if selected_evidence is None else selected_evidence,
        RecordingService(False) if service is None else service,
    )


def synthetic_write_evidence() -> tuple[ClaudeCapabilityEvidence, ...]:
    env = environment()
    replacements = {
        "can_validate_user_decisions": ClaudeCapabilityEvidence(
            env,
            "can_validate_user_decisions",
            ("UserPromptSubmit",),
            "test-only:synthetic-decision",
            EvidenceResult.PASS,
            "",
        ),
        "can_write": ClaudeCapabilityEvidence(
            env,
            "can_write",
            ("UserPromptSubmit",),
            "test-only:synthetic-write",
            EvidenceResult.PASS,
            "",
        ),
    }
    return tuple(replacements.get(item.capability_name, item) for item in evidence())


def raw(
    event_id: str,
    event_name: str,
    origin: RawOrigin = RawOrigin.LIFECYCLE,
    prompt: str | None = None,
    user_input_ref: str | None = None,
    session_id: str = "session-1",
) -> ClaudeRawEvent:
    return ClaudeRawEvent(
        event_id,
        event_name,
        session_id,
        NOW,
        origin,
        prompt,
        user_input_ref,
    )


def binding(
    actions: tuple[DecisionAction, ...] = (
        DecisionAction.SAVE,
        DecisionAction.EDIT,
        DecisionAction.SKIP,
    ),
) -> DecisionBinding:
    return DecisionBinding(
        "proposal-1",
        "create",
        ADAPTER_ID,
        "session-1",
        "digest-1",
        (("knowledge-1", 1),),
        actions,
    )


def resolution(reason: ControlReason, values: tuple[bool, bool, bool, bool]) -> ControlResolution:
    return ControlResolution(reason, *values, None)


def test_adapter_values_require_every_dataclass_field() -> None:
    for data_type in (ClaudeEnvironment, ClaudeCapabilityEvidence, ClaudeRawEvent):
        assert all(field.default is MISSING for field in fields(data_type))
        assert all(field.default_factory is MISSING for field in fields(data_type))


def test_adapter_values_reject_incomplete_environment_and_naive_event_time() -> None:
    with pytest.raises(HostContractError, match="environment"):
        ClaudeEnvironment("", "macOS", "arm64", "default")
    with pytest.raises(HostContractError, match="timezone-aware"):
        ClaudeRawEvent(
            "event",
            "SessionStart",
            "session-1",
            datetime(2026, 9, 14),
            RawOrigin.LIFECYCLE,
            None,
            None,
        )


def test_capabilities_match_exact_environment_and_keep_writes_blocked() -> None:
    selected = capabilities_for(environment(), evidence())
    assert {item.name: item.available for item in selected} == {
        "can_read": True,
        "can_search": True,
        "can_validate_user_decisions": False,
        "can_write": False,
        "can_observe_atomic_boundaries": False,
        "can_auto_activate": False,
    }
    another = ClaudeEnvironment("2.1.242", "macOS", "arm64", "default")
    assert not any(item.available for item in capabilities_for(another, evidence()))


def test_unproven_search_capability_prevents_service_call() -> None:
    service = RecordingService(True)
    host = adapter(service, ())
    result = host.search(
        SearchQuery("private scope", 1, None, (), (), ()),
        resolution(ControlReason.ACTIVE, (True, True, True, True)),
        ContextScope(None, None, "session-1"),
        (),
    )
    assert result is None
    assert host.last_memory_error is None


@pytest.mark.parametrize("failure", [TimeoutError("timeout"), object()])
def test_timeout_and_malformed_retrieval_fail_open(failure: BaseException | object) -> None:
    class BrokenSearchService(RecordingService):
        def search(self, query: object) -> Any:
            if isinstance(failure, BaseException):
                raise failure
            return failure

    host = adapter(BrokenSearchService(False))
    result = host.search(
        SearchQuery("approved", 1, None, (), (), ()),
        resolution(ControlReason.ACTIVE, (True, True, True, True)),
        ContextScope(None, None, "session-1"),
        (),
    )
    assert result is None
    expected = (
        "TimeoutError" if isinstance(failure, BaseException) else "MalformedRetrievalResponse"
    )
    assert host.last_memory_error == expected


@pytest.mark.parametrize("status", tuple(CommitStatus))
def test_only_committed_result_maps_to_saved(status: CommitStatus) -> None:
    result = CommitResult(status, (), None, None)
    assert is_saved_result(result) is (status is CommitStatus.COMMITTED)
    assert not is_saved_result({"status": "committed"})


def test_write_requires_both_write_and_decision_evidence() -> None:
    env = environment()
    write_only = ClaudeCapabilityEvidence(
        env, "can_write", (), "test:write", EvidenceResult.PASS, ""
    )
    assert not {item.name: item for item in capabilities_for(env, (write_only,))}[
        "can_write"
    ].available


def test_duplicate_capability_evidence_is_rejected() -> None:
    with pytest.raises(HostContractError, match="duplicate"):
        capabilities_for(environment(), evidence() + (evidence()[0],))


def test_public_plugin_commands_are_explicit_and_non_shell() -> None:
    assert plugin_commands("/tmp/expertiseos", "expertiseos") == (
        ("claude", "plugin", "install", "/tmp/expertiseos"),
        ("claude", "plugin", "uninstall", "expertiseos"),
    )
    with pytest.raises(HostContractError):
        plugin_commands("", "expertiseos")


def test_normalizes_only_supported_actual_origin_events() -> None:
    host = adapter()
    assert isinstance(host, HostAdapter)
    start = host.handle_raw_event(raw("start", "SessionStart"))
    user = host.handle_raw_event(
        raw("user", "UserPromptSubmit", RawOrigin.USER, "skip", "claude:user")
    )
    assert start.kind is EventKind.SESSION_START
    assert user.kind is EventKind.USER_INPUT
    assert user.action is DecisionAction.SKIP
    with pytest.raises(HostContractError, match="actual-user"):
        host.normalize(raw("model", "UserPromptSubmit", RawOrigin.MODEL, "save", None))
    with pytest.raises(HostContractError, match="unsupported"):
        host.normalize(raw("unknown", "Notification"))
    with pytest.raises(HostContractError, match="outside"):
        host.normalize(raw("other", "SessionStart", session_id="session-2"))


def test_nested_atomic_events_defer_comparison_and_reject_early_checkpoint() -> None:
    host = adapter()
    host.handle_raw_event(raw("start", "SessionStart"))
    host.handle_raw_event(raw("begin-1", "PreToolUse"))
    host.handle_raw_event(raw("begin-2", "PreToolUse"))
    assert host.atomic_depth == 2
    assert host.comparison_due
    with pytest.raises(HostContractError, match="ineligible"):
        host.handle_raw_event(raw("early", "Stop"))
    host.handle_raw_event(raw("end-1", "PostToolUse"))
    host.handle_raw_event(raw("end-2", "PostToolUseFailure"))
    host.handle_raw_event(raw("safe", "Stop"))
    assert host.atomic_depth == 0
    assert not host.comparison_due


def test_checkpoint_requires_proven_capability_and_c004_permission() -> None:
    host = adapter()
    host.handle_raw_event(raw("start", "SessionStart"))
    active = resolution(ControlReason.ACTIVE, (True, True, True, True))
    context = ContextScope(None, None, "session-1")
    assert not host.checkpoint_eligible(active, context, (), InteractionKind.COLLECTION)

    env = environment()
    atomic = ClaudeCapabilityEvidence(
        env,
        "can_observe_atomic_boundaries",
        ("PreToolUse", "PostToolUse", "Stop"),
        "test:live-atomic",
        EvidenceResult.PASS,
        "",
    )
    proven_evidence = tuple(
        atomic if item.capability_name == "can_observe_atomic_boundaries" else item
        for item in evidence()
    )
    proven = adapter(selected_evidence=proven_evidence)
    proven.handle_raw_event(raw("start", "SessionStart"))
    assert proven.checkpoint_eligible(active, context, (), InteractionKind.COLLECTION)


@pytest.mark.parametrize(
    ("reason", "values", "interaction", "expected"),
    [
        (ControlReason.DISABLED, (False, False, False, False), InteractionKind.RECALL, False),
        (ControlReason.PAUSED, (False, False, False, True), InteractionKind.RECALL, True),
        (ControlReason.FATIGUE_REST, (False, False, False, True), InteractionKind.OBSERVE, False),
        (
            ControlReason.TARGET_SATISFIED,
            (True, True, False, True),
            InteractionKind.COLLECTION,
            True,
        ),
        (ControlReason.ACTIVE, (True, True, True, True), InteractionKind.EXERCISE, True),
    ],
)
def test_interaction_consumes_control_resolution(
    reason: ControlReason,
    values: tuple[bool, bool, bool, bool],
    interaction: InteractionKind,
    expected: bool,
) -> None:
    assert (
        interaction_allowed(
            resolution(reason, values), ContextScope(None, None, "session-1"), (), interaction
        )
        is expected
    )


def test_scope_exclusion_denies_every_interaction() -> None:
    exclusion = ScopeExclusion(
        "excluded",
        ExclusionKind.SESSION,
        "session-1",
        NOW,
        "receipt-1",
    )
    active = resolution(ControlReason.ACTIVE, (True, True, True, True))
    context = ContextScope(None, None, "session-1")
    assert all(
        not interaction_allowed(active, context, (exclusion,), interaction)
        for interaction in InteractionKind
    )


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("Save", DecisionAction.SAVE),
        ("skip", DecisionAction.SKIP),
        ("Cancel", DecisionAction.SKIP),
        ("confirm change", DecisionAction.CONFIRM_CHANGE),
        ("Save: exact direct content", DecisionAction.SAVE),
        ("Edit: exact revised text", DecisionAction.EDIT),
        ('The assistant said "Save"', None),
        ("yes", None),
        ("edit this", None),
    ],
)
def test_only_explicit_controls_are_parsed(prompt: str, expected: DecisionAction | None) -> None:
    assert parse_explicit_action(prompt) is expected


def test_edit_and_direct_save_extract_only_explicit_content() -> None:
    assert explicit_edit_content("Edit: Exact Case") == "Exact Case"
    assert explicit_edit_content("edit this") is None
    assert direct_save_content("Save: Exact Claim", None) == "Exact Claim"
    assert direct_save_content("save this", " Immediate reference ") == "Immediate reference"
    assert direct_save_content("please save something useful", "reference") is None


def test_save_is_rejected_while_live_write_capability_is_unproven() -> None:
    host = adapter()
    host.handle_raw_event(raw("start", "SessionStart"))
    host.set_active_binding(binding())
    event = host.handle_raw_event(
        raw("save", "UserPromptSubmit", RawOrigin.USER, "save", "claude:save")
    )
    result = host.register_decision_if_unambiguous(event, binding())
    assert result.rejection is DecisionRejection.ACTION_NOT_ALLOWED
    assert not result.matched


def test_synthetic_future_write_path_requires_exact_active_binding_once() -> None:
    host = adapter(selected_evidence=synthetic_write_evidence())
    host.handle_raw_event(raw("start", "SessionStart"))
    current = binding()
    host.set_active_binding(current)
    changed_digest = DecisionBinding(
        current.proposal_id,
        current.operation_kind,
        current.adapter_id,
        current.session_id,
        "changed-digest",
        current.expected_versions,
        current.allowed_actions,
    )
    event = host.handle_raw_event(
        raw("save", "UserPromptSubmit", RawOrigin.USER, "save", "claude:save")
    )
    assert host.register_decision_if_unambiguous(event, changed_digest).rejection is (
        DecisionRejection.ACTION_NOT_ALLOWED
    )
    assert host.register_decision_if_unambiguous(event, current).matched
    assert host.register_decision_if_unambiguous(event, current).rejection is (
        DecisionRejection.ALREADY_OBSERVED
    )


def test_foreign_adapter_and_changed_versions_cannot_match_active_binding() -> None:
    host = adapter(selected_evidence=synthetic_write_evidence())
    host.handle_raw_event(raw("start", "SessionStart"))
    current = binding()
    host.set_active_binding(current)
    event = host.handle_raw_event(
        raw("save", "UserPromptSubmit", RawOrigin.USER, "save", "claude:save")
    )
    foreign = DecisionBinding(
        current.proposal_id,
        current.operation_kind,
        "codex",
        current.session_id,
        current.content_digest,
        current.expected_versions,
        current.allowed_actions,
    )
    changed_versions = DecisionBinding(
        current.proposal_id,
        current.operation_kind,
        current.adapter_id,
        current.session_id,
        current.content_digest,
        (("knowledge-1", 2),),
        current.allowed_actions,
    )
    assert host.register_decision_if_unambiguous(event, foreign).rejection is (
        DecisionRejection.WRONG_ADAPTER
    )
    assert host.register_decision_if_unambiguous(event, changed_versions).rejection is (
        DecisionRejection.ACTION_NOT_ALLOWED
    )


def test_skip_declines_but_ambiguous_event_expires_without_grant() -> None:
    service = RecordingService(False)
    host = adapter(service)
    host.handle_raw_event(raw("start", "SessionStart"))
    decision = binding()
    host.set_active_binding(decision)
    skip = host.handle_raw_event(
        raw("skip", "UserPromptSubmit", RawOrigin.USER, "skip", "claude:skip")
    )
    assert host.register_decision_if_unambiguous(skip, decision).matched
    assert service.declined == ["proposal-1"]

    host.set_active_binding(decision)
    ambiguous = host.handle_raw_event(
        raw("other", "UserPromptSubmit", RawOrigin.USER, "continue work", "claude:other")
    )
    result = host.register_decision_if_unambiguous(ambiguous, decision)
    assert result.rejection is DecisionRejection.AMBIGUOUS_ACTION
    assert service.unrelated == [("session-1", None)]


def test_session_end_clears_state_even_when_service_fails() -> None:
    service = RecordingService(True)
    host = adapter(service)
    host.handle_raw_event(raw("start", "SessionStart"))
    host.set_active_binding(binding())
    host.handle_raw_event(raw("end", "SessionEnd"))
    assert host.last_memory_error == "ConnectionError"
    with pytest.raises(HostContractError, match="ended"):
        host.handle_raw_event(raw("late", "Stop"))


def test_abrupt_session_end_clears_open_atomic_state_and_expires_service_session() -> None:
    service = RecordingService(False)
    host = adapter(service)
    host.handle_raw_event(raw("start", "SessionStart"))
    host.handle_raw_event(raw("begin", "PreToolUse"))
    host.handle_raw_event(raw("end", "SessionEnd"))
    assert host.atomic_depth == 0
    assert service.expired_sessions == ["session-1"]
