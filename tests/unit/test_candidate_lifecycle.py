#!/usr/bin/env python3
# Purpose: Test src/expertiseos/domain/candidate_store.py legal and illegal transitions.

from __future__ import annotations

import pytest

from expertiseos.approval.gate import canonical_approval_digest
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.domain.errors import CandidateTransitionError
from expertiseos.domain.models import (
    CandidateState,
    CreateOperation,
    PendingOperation,
    PendingOperationKind,
)
from tests.consent_support import NOW, approved


def proposal(proposal_id: str = "proposal-1", session_id: str = "session-1") -> PendingOperation:
    payload = CreateOperation(approved("candidate"))
    digest = canonical_approval_digest(PendingOperationKind.CREATE, payload, ())
    return PendingOperation(
        proposal_id,
        f"operation-{proposal_id}",
        session_id,
        "codex",
        PendingOperationKind.CREATE,
        CandidateState.DETECTED,
        payload,
        digest,
        (),
        NOW,
    )


def test_complete_legal_lifecycle() -> None:
    store = CandidateStore()
    store.create_detected(proposal())
    assert store.mark_awaiting_checkpoint("proposal-1").state is CandidateState.AWAITING_CHECKPOINT
    assert store.mark_awaiting_decision("proposal-1").state is CandidateState.AWAITING_DECISION
    assert store.mark_approved("proposal-1").state is CandidateState.APPROVED


@pytest.mark.parametrize("terminal", ["decline", "expire"])
def test_any_unresolved_state_may_terminate(terminal: str) -> None:
    for index, advance in enumerate((0, 1, 2)):
        store = CandidateStore()
        item = proposal(f"p-{index}")
        store.create_detected(item)
        if advance >= 1:
            store.mark_awaiting_checkpoint(item.proposal_id)
        if advance == 2:
            store.mark_awaiting_decision(item.proposal_id)
        result = (
            store.decline(item.proposal_id, None)
            if terminal == "decline"
            else store.expire(item.proposal_id)
        )
        assert result.state.value == f"{terminal}d"


def test_illegal_and_terminal_transitions_preserve_state() -> None:
    store = CandidateStore()
    store.create_detected(proposal())
    with pytest.raises(CandidateTransitionError):
        store.mark_awaiting_decision("proposal-1")
    assert store.get("proposal-1").state is CandidateState.DETECTED  # type: ignore[union-attr]
    store.expire("proposal-1")
    with pytest.raises(CandidateTransitionError):
        store.mark_awaiting_checkpoint("proposal-1")
    assert store.get("proposal-1").state is CandidateState.EXPIRED  # type: ignore[union-attr]


def test_session_expiry_affects_only_unresolved_proposals() -> None:
    store = CandidateStore()
    store.create_detected(proposal("p1", "s1"))
    store.create_detected(proposal("p2", "s2"))
    assert store.expire_session("s1") == ("p1",)
    assert store.get("p1").state is CandidateState.EXPIRED  # type: ignore[union-attr]
    assert store.get("p2").state is CandidateState.DETECTED  # type: ignore[union-attr]
