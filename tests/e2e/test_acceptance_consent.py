#!/usr/bin/env python3
# Purpose: Test src/expertiseos consent boundaries for acceptance cases AT-04 through AT-06.

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from expertiseos.approval.gate import ApprovalGate, DecisionGrantStore
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.domain.errors import ApprovalRejectedError
from expertiseos.domain.models import CommitStatus, PendingOperation
from expertiseos.hosts.contract import DecisionAction, DecisionBinding, EventKind, HostEvent
from expertiseos.knowledge.backend import SearchQuery
from expertiseos.knowledge.service import KnowledgeService
from expertiseos.state.sqlite import SQLiteState
from tests.consent_support import (
    NOW,
    ServiceBundle,
    approved,
    fake_backend,
    observation,
)
from tests.fakes import DeterministicClock, FakeHostAdapter


def test_at04_exact_approved_proposal_and_receipt_are_durable(tmp_path: Path) -> None:
    state_path = tmp_path / "state.db"
    backend = fake_backend()
    candidates = CandidateStore()
    grants = DecisionGrantStore()
    receipts = SQLiteState(state_path)
    service = KnowledgeService(
        backend,
        candidates,
        grants,
        ApprovalGate(),
        receipts,
        DeterministicClock(NOW + timedelta(hours=1), timedelta(seconds=1)),
    )
    value = approved(
        "exact acceptance knowledge",
        categories=("procedure",),
        subjects=("domain", "self"),
        source_refs=("host-user-at04",),
    )
    proposal = service.propose_create(
        "proposal-at04", "operation-at04", "session-at04", "codex", value, NOW
    )
    service.present(proposal.proposal_id)
    grant = service.register_decision(
        proposal.proposal_id,
        "grant-at04",
        observation(user_event_ref="host-user-at04"),
        NOW + timedelta(seconds=1),
    )

    result = service.commit(proposal.proposal_id, grant.grant_id, proposal.operation_id)

    assert result.status is CommitStatus.COMMITTED
    assert result.receipt is not None
    assert result.receipt.content_digest == proposal.content_digest
    assert result.records[0].categories == ("procedure",)
    assert result.records[0].subjects == ("domain", "self")
    assert result.records[0].source_refs == ("host-user-at04",)
    assert receipts.get_receipt("operation-at04") == result.receipt
    receipts.close()


def test_at05_decline_and_restart_leave_no_candidate_content(tmp_path: Path) -> None:
    state_path = tmp_path / "state.db"
    backend = fake_backend()
    candidates = CandidateStore()
    grants = DecisionGrantStore()
    receipts = SQLiteState(state_path)
    service = KnowledgeService(
        backend,
        candidates,
        grants,
        ApprovalGate(),
        receipts,
        DeterministicClock(NOW + timedelta(hours=1), timedelta(seconds=1)),
    )
    cases = ("skip", "cancel", "ignore", "session-end", "crash")
    proposals: dict[str, PendingOperation] = {}
    for case in cases:
        proposal = service.propose_create(
            f"proposal-at05-{case}",
            f"operation-at05-{case}",
            f"session-at05-{case}",
            "codex",
            approved(f"UNAPPROVED_AT05_{case.upper()}_MARKER"),
            NOW,
        )
        service.present(proposal.proposal_id)
        proposals[case] = proposal

    service.decline(proposals["skip"].proposal_id, "fingerprint-at05-skip")
    service.decline(proposals["cancel"].proposal_id, None)
    service.expire_unrelated_decisions("session-at05-ignore", None)
    service.expire_session("session-at05-session-end")
    receipts.close()

    reopened = SQLiteState(state_path)
    restarted_candidates = CandidateStore()
    restarted_grants = DecisionGrantStore()
    for case, proposal in proposals.items():
        marker = f"UNAPPROVED_AT05_{case.upper()}_MARKER"
        assert reopened.get_receipt(f"operation-at05-{case}") is None
        assert backend.search(SearchQuery(marker, 10, None)) == ()
        assert restarted_candidates.get(proposal.proposal_id) is None
        assert restarted_grants.get(f"grant-at05-{case}") is None
    reopened.close()


def test_at06_forged_or_ambiguous_events_cannot_authorize_write() -> None:
    backend = fake_backend()
    candidates = CandidateStore()
    grants = DecisionGrantStore()
    receipts = SQLiteState(":memory:")
    service = KnowledgeService(
        backend,
        candidates,
        grants,
        ApprovalGate(),
        receipts,
        DeterministicClock(NOW + timedelta(hours=1), timedelta(seconds=1)),
    )
    bundle = ServiceBundle(service, backend, candidates, grants, receipts)
    proposal = bundle.service.propose_create(
        "proposal-at06",
        "operation-at06",
        "session-at06",
        "codex",
        approved("forged approval marker"),
        NOW,
    )
    bundle.service.present(proposal.proposal_id)

    host = FakeHostAdapter("codex", "session-at06", ())
    host.on_session_start(
        HostEvent(
            "start-at06",
            "codex",
            "session-at06",
            EventKind.SESSION_START,
            NOW,
            None,
            None,
        )
    )
    ambiguous_event = HostEvent(
        "event-at06",
        "codex",
        "session-at06",
        EventKind.USER_INPUT,
        NOW + timedelta(seconds=1),
        "host-user-at06",
        None,
    )
    host.on_user_event(ambiguous_event)
    rejected_observation = host.register_decision_if_unambiguous(
        ambiguous_event,
        DecisionBinding(
            proposal.proposal_id,
            "create",
            "codex",
            "session-at06",
            proposal.content_digest,
            (),
            (DecisionAction.SAVE,),
        ),
    )

    with pytest.raises(ApprovalRejectedError):
        service.register_decision(proposal.proposal_id, "forged-grant", rejected_observation, NOW)
    result = service.commit(proposal.proposal_id, "forged-grant", "operation-at06")
    assert result.status is CommitStatus.REJECTED
    assert backend.search(SearchQuery("forged approval marker", 10, None)) == ()
    assert receipts.get_receipt("operation-at06") is None
    receipts.close()
