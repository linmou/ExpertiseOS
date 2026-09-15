#!/usr/bin/env python3
# Purpose: Test src/expertiseos/hosts/claude_code.py against promoted consent,
# retrieval, and control producers.

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from expertiseos.approval.gate import canonical_approval_digest
from expertiseos.domain.models import CommitStatus, CreateOperation, PendingOperationKind
from expertiseos.hosts.claude_code import (
    ADAPTER_ID,
    ClaudeCapabilityEvidence,
    ClaudeCodeAdapter,
    ClaudeEnvironment,
    ClaudeRawEvent,
    EvidenceResult,
    RawOrigin,
)
from expertiseos.hosts.contract import DecisionAction, DecisionBinding, DecisionRejection
from expertiseos.knowledge.backend import (
    IndexState,
    RetrievalResponse,
    SearchMode,
    SearchQuery,
    StoreState,
    TrustLevel,
)
from expertiseos.learning.controls import (
    ContextScope,
    ControlReason,
    ControlResolution,
    ExclusionKind,
    ScopeExclusion,
)
from tests.consent_support import NOW, approved, present_create, service_bundle

pytestmark = pytest.mark.integration
ENVIRONMENT = ClaudeEnvironment("2.1.241", "macOS 15.1.1 build 24B91", "arm64", "default")


def unavailable_evidence() -> tuple[ClaudeCapabilityEvidence, ...]:
    return tuple(
        ClaudeCapabilityEvidence(
            ENVIRONMENT,
            name,
            (),
            f"g0:claude:{name}",
            EvidenceResult.NOT_RUN,
            "authenticated live fixture not run",
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


def read_evidence() -> tuple[ClaudeCapabilityEvidence, ...]:
    evidence = list(unavailable_evidence())
    evidence[0] = ClaudeCapabilityEvidence(
        ENVIRONMENT, "can_read", (), "g0:shared-read", EvidenceResult.PASS, ""
    )
    evidence[1] = ClaudeCapabilityEvidence(
        ENVIRONMENT, "can_search", (), "g0:shared-search", EvidenceResult.PASS, ""
    )
    return tuple(evidence)


def synthetic_write_evidence() -> tuple[ClaudeCapabilityEvidence, ...]:
    evidence = list(read_evidence())
    evidence[2] = ClaudeCapabilityEvidence(
        ENVIRONMENT,
        "can_validate_user_decisions",
        ("UserPromptSubmit",),
        "test-only:synthetic-decision",
        EvidenceResult.PASS,
        "",
    )
    evidence[3] = ClaudeCapabilityEvidence(
        ENVIRONMENT,
        "can_write",
        ("UserPromptSubmit",),
        "test-only:synthetic-write",
        EvidenceResult.PASS,
        "",
    )
    return tuple(evidence)


def raw(
    event_id: str,
    event_name: str,
    prompt: str | None = None,
    user_ref: str | None = None,
) -> ClaudeRawEvent:
    origin = RawOrigin.USER if event_name == "UserPromptSubmit" else RawOrigin.LIFECYCLE
    return ClaudeRawEvent(
        event_id,
        event_name,
        "claude-session",
        datetime(2026, 9, 14, tzinfo=UTC),
        origin,
        prompt,
        user_ref,
    )


def active_resolution() -> ControlResolution:
    return ControlResolution(ControlReason.ACTIVE, True, True, True, True, None)


def test_actual_c003_result_reaches_claude_with_identity_and_trust_unchanged() -> None:
    bundle = service_bundle()
    proposal_id, grant_id = present_create(
        bundle,
        "approved shared object",
        session_id="producer-session",
        adapter_id="codex",
    )
    committed = bundle.service.commit(proposal_id, grant_id, "operation-1")
    host = ClaudeCodeAdapter("claude-session", ENVIRONMENT, read_evidence(), bundle.service)
    response = host.search(
        SearchQuery("shared object", 1, None, (), (), ()),
        active_resolution(),
        ContextScope(None, None, "claude-session"),
        (),
    )
    assert response is not None
    assert response.results[0].knowledge_id == committed.records[0].id
    assert response.results[0].version == committed.records[0].version
    assert response.results[0].trust is TrustLevel.UNTRUSTED_DATA
    assert len(response.results) == 1


def test_c004_disable_and_exclusion_prevent_service_retrieval() -> None:
    bundle = service_bundle()
    host = ClaudeCodeAdapter("claude-session", ENVIRONMENT, read_evidence(), bundle.service)
    query = SearchQuery("anything", 1, None, (), (), ())
    context = ContextScope(None, None, "claude-session")
    disabled = ControlResolution(ControlReason.DISABLED, False, False, False, False, None)
    assert host.search(query, disabled, context, ()) is None
    exclusion = ScopeExclusion(
        "excluded-session",
        ExclusionKind.SESSION,
        "claude-session",
        NOW,
        "receipt-1",
    )
    assert host.search(query, active_resolution(), context, (exclusion,)) is None


def test_session_end_expires_real_c002_proposal_and_late_save_cannot_match() -> None:
    bundle = service_bundle()
    proposal = bundle.service.propose_create(
        "claude-proposal",
        "claude-operation",
        "claude-session",
        ADAPTER_ID,
        approved("volatile candidate marker"),
        NOW,
    )
    bundle.service.present(proposal.proposal_id)
    host = ClaudeCodeAdapter("claude-session", ENVIRONMENT, read_evidence(), bundle.service)
    host.handle_raw_event(raw("start", "SessionStart"))
    binding = DecisionBinding(
        proposal.proposal_id,
        proposal.kind.value,
        ADAPTER_ID,
        "claude-session",
        proposal.content_digest,
        proposal.expected_versions,
        (DecisionAction.SAVE,),
    )
    host.set_active_binding(binding)
    host.handle_raw_event(raw("end", "SessionEnd"))
    assert bundle.candidates.get(proposal.proposal_id) is not None
    assert bundle.candidates.get(proposal.proposal_id).state.value == "expired"  # type: ignore[union-attr]
    late = ClaudeRawEvent(
        "late-save",
        "UserPromptSubmit",
        "claude-session",
        NOW,
        RawOrigin.USER,
        "save",
        "claude:late-save",
    )
    result = host.register_decision_if_unambiguous(host.normalize(late), binding)
    assert result.rejection is DecisionRejection.SESSION_ENDED
    assert bundle.receipts.get_receipt("claude-operation") is None


def test_unproven_live_save_cannot_enter_real_c002_grant_or_commit_path() -> None:
    bundle = service_bundle()
    proposal = bundle.service.propose_create(
        "claude-proposal",
        "claude-operation",
        "claude-session",
        ADAPTER_ID,
        approved("blocked candidate marker"),
        NOW,
    )
    bundle.service.present(proposal.proposal_id)
    host = ClaudeCodeAdapter("claude-session", ENVIRONMENT, read_evidence(), bundle.service)
    host.handle_raw_event(raw("start", "SessionStart"))
    event = host.handle_raw_event(raw("save", "UserPromptSubmit", "save", "claude:actual-user"))
    binding = DecisionBinding(
        proposal.proposal_id,
        proposal.kind.value,
        ADAPTER_ID,
        "claude-session",
        proposal.content_digest,
        proposal.expected_versions,
        (DecisionAction.SAVE,),
    )
    host.set_active_binding(binding)
    observation = host.register_decision_if_unambiguous(event, binding)
    assert observation.rejection is DecisionRejection.ACTION_NOT_ALLOWED
    assert bundle.grants.get("grant-1") is None
    assert bundle.receipts.get_receipt("claude-operation") is None
    assert (
        bundle.backend.search(SearchQuery("blocked candidate marker", 10, None, (), (), ())) == ()
    )


def test_synthetic_future_write_path_uses_real_c002_exactly_once_without_promoting_g0() -> None:
    bundle = service_bundle()
    proposal = bundle.service.propose_create(
        "claude-proposal",
        "claude-operation",
        "claude-session",
        ADAPTER_ID,
        approved("synthetic approved marker"),
        NOW,
    )
    bundle.service.present(proposal.proposal_id)
    host = ClaudeCodeAdapter(
        "claude-session", ENVIRONMENT, synthetic_write_evidence(), bundle.service
    )
    host.handle_raw_event(raw("start", "SessionStart"))
    binding = DecisionBinding(
        proposal.proposal_id,
        proposal.kind.value,
        ADAPTER_ID,
        "claude-session",
        proposal.content_digest,
        proposal.expected_versions,
        (DecisionAction.SAVE,),
    )
    host.set_active_binding(binding)
    event = host.handle_raw_event(
        raw("save", "UserPromptSubmit", "save", "test-only:synthetic-user")
    )
    observation = host.register_decision_if_unambiguous(event, binding)
    grant = bundle.service.register_decision(proposal.proposal_id, "grant-1", observation, NOW)
    first = bundle.service.commit(proposal.proposal_id, grant.grant_id, "claude-operation")
    second = bundle.service.commit(proposal.proposal_id, grant.grant_id, "claude-operation")
    assert first.status is CommitStatus.COMMITTED
    assert second.status is CommitStatus.COMMITTED
    assert first.records == second.records
    assert first.records[0].version == 1


def test_explicit_edit_replaces_digest_and_requires_a_fresh_save_event() -> None:
    bundle = service_bundle()
    proposal = bundle.service.propose_create(
        "claude-proposal",
        "claude-operation",
        "claude-session",
        ADAPTER_ID,
        approved("original text"),
        NOW,
    )
    bundle.service.present(proposal.proposal_id)
    host = ClaudeCodeAdapter(
        "claude-session", ENVIRONMENT, synthetic_write_evidence(), bundle.service
    )
    host.handle_raw_event(raw("start", "SessionStart"))
    original_binding = DecisionBinding(
        proposal.proposal_id,
        proposal.kind.value,
        ADAPTER_ID,
        "claude-session",
        proposal.content_digest,
        proposal.expected_versions,
        (DecisionAction.EDIT, DecisionAction.SAVE),
    )
    host.set_active_binding(original_binding)
    edit_event = host.handle_raw_event(
        raw("edit", "UserPromptSubmit", "Edit: revised exact text", "test-only:edit")
    )
    assert host.register_decision_if_unambiguous(edit_event, original_binding).action is (
        DecisionAction.EDIT
    )
    revised = bundle.service.revise_displayed_proposal(
        proposal.proposal_id, CreateOperation(approved("revised exact text"))
    )
    assert revised.content_digest != original_binding.content_digest
    revised_binding = DecisionBinding(
        revised.proposal_id,
        revised.kind.value,
        ADAPTER_ID,
        "claude-session",
        revised.content_digest,
        revised.expected_versions,
        (DecisionAction.SAVE,),
    )
    host.set_active_binding(revised_binding)
    save_event = host.handle_raw_event(
        raw("save-after-edit", "UserPromptSubmit", "save", "test-only:save-after-edit")
    )
    assert host.register_decision_if_unambiguous(save_event, original_binding).rejection is (
        DecisionRejection.ACTION_NOT_ALLOWED
    )
    assert host.register_decision_if_unambiguous(save_event, revised_binding).matched


def test_exact_direct_save_uses_normal_c002_proposal_and_grant_path() -> None:
    bundle = service_bundle()
    value = approved("direct exact text", source_refs=("test-only:direct-save",))
    digest = canonical_approval_digest(PendingOperationKind.CREATE, CreateOperation(value), ())
    binding = DecisionBinding(
        "direct-proposal",
        PendingOperationKind.CREATE.value,
        ADAPTER_ID,
        "claude-session",
        digest,
        (),
        (DecisionAction.SAVE,),
    )
    host = ClaudeCodeAdapter(
        "claude-session", ENVIRONMENT, synthetic_write_evidence(), bundle.service
    )
    host.handle_raw_event(raw("start", "SessionStart"))
    host.set_active_binding(binding)
    event = host.handle_raw_event(
        raw(
            "direct-save",
            "UserPromptSubmit",
            "Save: direct exact text",
            "test-only:direct-save",
        )
    )
    observation = host.register_decision_if_unambiguous(event, binding)
    proposal, grant = bundle.service.propose_direct_create(
        "direct-proposal",
        "direct-operation",
        "claude-session",
        ADAPTER_ID,
        value,
        observation,
        "direct-grant",
        NOW,
    )
    result = bundle.service.commit(proposal.proposal_id, grant.grant_id, "direct-operation")
    assert result.status is CommitStatus.COMMITTED
    assert result.records[0].content == "direct exact text"


def test_stale_concurrent_revision_returns_conflict_without_overwrite() -> None:
    bundle = service_bundle()
    current = bundle.backend.create_approved(approved("version one"), "seed-operation")
    proposal = bundle.service.propose_revision(
        "revision-proposal",
        "revision-operation",
        "claude-session",
        ADAPTER_ID,
        current.id,
        current.version,
        approved("claude revision"),
        NOW,
    )
    bundle.service.present(proposal.proposal_id)
    host = ClaudeCodeAdapter(
        "claude-session", ENVIRONMENT, synthetic_write_evidence(), bundle.service
    )
    host.handle_raw_event(raw("start", "SessionStart"))
    binding = DecisionBinding(
        proposal.proposal_id,
        proposal.kind.value,
        ADAPTER_ID,
        "claude-session",
        proposal.content_digest,
        proposal.expected_versions,
        (DecisionAction.SAVE,),
    )
    host.set_active_binding(binding)
    event = host.handle_raw_event(raw("save", "UserPromptSubmit", "save", "test-only:stale-save"))
    observation = host.register_decision_if_unambiguous(event, binding)
    grant = bundle.service.register_decision(
        proposal.proposal_id, "revision-grant", observation, NOW
    )
    other = bundle.backend.update_approved(
        current.id, current.version, approved("other host revision"), "other-operation"
    )
    result = bundle.service.commit(proposal.proposal_id, grant.grant_id, "revision-operation")
    assert result.status is CommitStatus.CONFLICT
    assert bundle.backend.get(current.id, None, False) == other


def test_service_outage_is_contained_and_host_task_result_remains_available() -> None:
    class UnavailableService:
        def search(self, query: SearchQuery) -> RetrievalResponse:
            raise ConnectionError("service unavailable")

        def decline(self, proposal_id: str, fingerprint: str | None) -> object:
            raise ConnectionError("service unavailable")

        def expire_session(self, session_id: str) -> tuple[str, ...]:
            raise ConnectionError("service unavailable")

        def expire_unrelated_decisions(
            self, session_id: str, active_proposal_id: str | None
        ) -> tuple[str, ...]:
            raise ConnectionError("service unavailable")

    host_result = "task-complete"
    host = ClaudeCodeAdapter("claude-session", ENVIRONMENT, read_evidence(), UnavailableService())
    result = host.search(
        SearchQuery("approved", 1, None, (), (), ()),
        active_resolution(),
        ContextScope(None, None, "claude-session"),
        (),
    )
    assert result is None
    assert host.last_memory_error == "ConnectionError"
    assert host_result == "task-complete"


def test_retrieval_and_host_switch_do_not_touch_learning_state() -> None:
    class LearningGuardService:
        def __init__(self) -> None:
            self.search_calls = 0
            self.learning_calls = 0

        def search(self, query: SearchQuery) -> RetrievalResponse:
            self.search_calls += 1
            return RetrievalResponse(
                (), SearchMode.KEYWORD, True, StoreState.READY, IndexState.READY, False
            )

        def decline(self, proposal_id: str, fingerprint: str | None) -> object:
            return object()

        def expire_session(self, session_id: str) -> tuple[str, ...]:
            return ()

        def expire_unrelated_decisions(
            self, session_id: str, active_proposal_id: str | None
        ) -> tuple[str, ...]:
            return ()

    service = LearningGuardService()
    host = ClaudeCodeAdapter("claude-session", ENVIRONMENT, read_evidence(), service)
    host.search(
        SearchQuery("approved", 1, None, (), (), ()),
        active_resolution(),
        ContextScope(None, None, "claude-session"),
        (),
    )
    assert service.search_calls == 1
    assert service.learning_calls == 0
