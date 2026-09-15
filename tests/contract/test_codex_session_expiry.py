#!/usr/bin/env python3
# Purpose: Test src/expertiseos/hosts/codex.py expires volatile C002 state on session end.

import hashlib
from datetime import UTC, datetime

import pytest

from expertiseos.approval.gate import DecisionGrantStore
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.domain.models import (
    CandidateState,
    CreateOperation,
    PendingOperation,
    PendingOperationKind,
)
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
from expertiseos.knowledge.backend import ApprovedKnowledgeInput

NOW = datetime(2026, 9, 14, tzinfo=UTC)


def event(identifier: str, kind: EventKind) -> HostEvent:
    return HostEvent(identifier, "codex", "session-1", kind, NOW, None, None)


def pending() -> PendingOperation:
    content = "candidate marker"
    digest = hashlib.sha256(content.encode()).hexdigest()
    value = ApprovedKnowledgeInput(content, digest, (), ("domain",), None, None, (), "user")
    return PendingOperation(
        "proposal-1",
        "operation-1",
        "session-1",
        "codex",
        PendingOperationKind.CREATE,
        CandidateState.AWAITING_DECISION,
        CreateOperation(value),
        digest,
        (),
        NOW,
    )


def test_session_end_expires_candidate_grant_and_adapter_binding() -> None:
    candidates = CandidateStore()
    proposal = pending()
    candidates.create_detected(
        PendingOperation(
            proposal.proposal_id,
            proposal.operation_id,
            proposal.session_id,
            proposal.adapter_id,
            proposal.kind,
            CandidateState.DETECTED,
            proposal.payload,
            proposal.content_digest,
            proposal.expected_versions,
            proposal.created_at,
        )
    )
    candidates.mark_awaiting_checkpoint(proposal.proposal_id)
    candidates.mark_awaiting_decision(proposal.proposal_id)
    grants = DecisionGrantStore()
    grant = grants.register(
        proposal,
        DecisionObservation(True, DecisionAction.SAVE, "turn-1", DecisionRejection.NONE),
        "grant-1",
        NOW,
    )
    host = CodexAdapter(
        CodexEnvironment("0.146.1", "macOS 15.1.1 build 24B91", "arm64", "workspace-write"),
        "session-1",
        candidates,
        grants,
    )
    host.on_session_start(event("start", EventKind.SESSION_START))
    host.display_proposal(
        DecisionBinding(
            proposal.proposal_id,
            proposal.kind.value,
            "codex",
            "session-1",
            proposal.content_digest,
            (),
            (DecisionAction.SAVE,),
        )
    )

    host.on_session_end(event("end", EventKind.SESSION_END))

    assert candidates.get(proposal.proposal_id).state is CandidateState.EXPIRED  # type: ignore[union-attr]
    assert grants.get(grant.grant_id) is None
    assert host.active_binding is None


def test_abrupt_end_cleans_unknown_atomic_state() -> None:
    host = CodexAdapter(
        CodexEnvironment("0.146.1", "macOS 15.1.1 build 24B91", "arm64", "workspace-write"),
        "session-1",
        CandidateStore(),
        DecisionGrantStore(),
    )
    host.on_session_start(event("start", EventKind.SESSION_START))
    host.on_atomic_begin(event("begin", EventKind.ATOMIC_BEGIN))
    host.mark_comparison_due()
    host.on_session_end(event("end", EventKind.SESSION_END))
    assert not host.comparison_ready
    with pytest.raises(HostContractError, match="session already ended"):
        host.on_user_event(
            HostEvent(
                "late",
                "codex",
                "session-1",
                EventKind.USER_INPUT,
                NOW,
                "turn-late",
                None,
            )
        )


def test_repeated_session_end_is_rejected() -> None:
    host = CodexAdapter(
        CodexEnvironment("0.146.1", "macOS 15.1.1 build 24B91", "arm64", "read-only"),
        "session-1",
        CandidateStore(),
        DecisionGrantStore(),
    )
    host.on_session_start(event("start", EventKind.SESSION_START))
    host.on_session_end(event("end", EventKind.SESSION_END))
    with pytest.raises(HostContractError, match="session already ended"):
        host.on_session_end(event("end-2", EventKind.SESSION_END))
