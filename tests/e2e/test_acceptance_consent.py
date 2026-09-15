#!/usr/bin/env python3
# Purpose: Test src/expertiseos consent boundaries for acceptance cases AT-04 through AT-06.

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from expertiseos.approval.gate import ApprovalGate, DecisionGrantStore
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.domain.errors import ApprovalRejectedError
from expertiseos.domain.models import CommitStatus, LearnerState, PendingOperation
from expertiseos.hosts.contract import DecisionAction, DecisionBinding, EventKind, HostEvent
from expertiseos.knowledge.backend import SearchQuery
from expertiseos.knowledge.service import KnowledgeService
from expertiseos.learning.evidence import AssistanceLevel, EvidenceOutcome, LearnerEvidence
from expertiseos.service import ExpertiseOSService, ToolStatus
from expertiseos.state.sqlite import SQLiteState
from tests.consent_support import (
    NOW,
    ServiceBundle,
    approved,
    fake_backend,
    observation,
)
from tests.e2e.conftest import ProductGraph
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
        assert backend.search(SearchQuery(marker, 10, None, (), (), ())) == ()
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
    assert backend.search(SearchQuery("forged approval marker", 10, None, (), (), ())) == ()
    assert receipts.get_receipt("operation-at06") is None
    receipts.close()


def test_c008_operation_id_is_the_only_commit_replay_identity(tmp_path: Path) -> None:
    state_path = tmp_path / "state-c008.db"
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
    facade = ExpertiseOSService(service, backend, receipts, ())
    proposal = service.propose_create(
        "proposal-c008",
        "operation-c008",
        "session-c008",
        "codex",
        approved("canonical operation identity"),
        NOW,
    )
    service.present(proposal.proposal_id)
    service.register_decision(
        proposal.proposal_id,
        "grant-c008",
        observation(user_event_ref="host-user-c008"),
        NOW + timedelta(seconds=1),
    )

    wrong = facade.commit_proposal(proposal.proposal_id, "grant-c008", "request-c008", {})
    committed = facade.commit_proposal(
        proposal.proposal_id, "grant-c008", proposal.operation_id, {}
    )

    assert wrong.status is ToolStatus.REJECTED
    assert wrong.message != "Saved"
    assert committed.status is ToolStatus.COMMITTED
    assert committed.message == "Saved"
    receipts.close()


def test_at07_saved_knowledge_and_learning_evidence_require_separate_approval(
    product_graph: ProductGraph,
) -> None:
    facade = ExpertiseOSService(
        product_graph.knowledge,
        product_graph.backend,
        product_graph.state,
        (),
    )
    proposed = facade.propose_create_knowledge(
        "proposal-at07-knowledge",
        "operation-at07-knowledge",
        "session-at07",
        "codex",
        approved("AT-07 approved knowledge"),
        NOW,
    )
    assert proposed.status is ToolStatus.OK
    product_graph.knowledge.register_decision(
        "proposal-at07-knowledge",
        "grant-at07-knowledge",
        observation(user_event_ref="host-user-at07-knowledge"),
        NOW + timedelta(seconds=1),
    )
    saved = facade.commit_proposal(
        "proposal-at07-knowledge",
        "grant-at07-knowledge",
        "operation-at07-knowledge",
        {},
    )
    assert saved.status is ToolStatus.COMMITTED
    record = saved.data.records[0]  # type: ignore[union-attr]
    assert product_graph.state.list_evidence(record.id, record.version, None, 20) == ()

    evidence = LearnerEvidence(
        "evidence-at07",
        record.id,
        record.version,
        "task-at07",
        "session-at07",
        "apply approved knowledge",
        EvidenceOutcome.PASS,
        AssistanceLevel.INDEPENDENT,
        None,
        "user contribution",
        LearnerState.RECOGNIZED,
        LearnerState.RECOGNIZED,
        False,
        "operation-at07-evidence",
        NOW,
    )
    evidence_proposal = facade.propose_learning_evidence(
        "proposal-at07-evidence",
        "operation-at07-evidence",
        "session-at07",
        "codex",
        evidence,
        {record.id: record.version},
        NOW,
    )
    assert evidence_proposal.status is ToolStatus.OK
    rejected = facade.commit_proposal(
        "proposal-at07-evidence",
        "missing-grant-at07",
        "operation-at07-evidence",
        {record.id: record.version},
    )
    assert rejected.status is ToolStatus.REJECTED
    assert product_graph.state.list_evidence(record.id, record.version, None, 20) == ()
    product_graph.knowledge.register_decision(
        "proposal-at07-evidence",
        "grant-at07-evidence",
        observation(user_event_ref="host-user-at07-evidence"),
        NOW + timedelta(seconds=2),
    )
    committed = facade.commit_proposal(
        "proposal-at07-evidence",
        "grant-at07-evidence",
        "operation-at07-evidence",
        {record.id: record.version},
    )
    assert committed.status is ToolStatus.COMMITTED
    assert product_graph.state.list_evidence(record.id, record.version, None, 20) == (evidence,)


def test_at08_revision_is_separately_approved_and_decline_preserves_state(
    product_graph: ProductGraph,
) -> None:
    original = product_graph.backend.create_approved(
        approved("original scope"),
        "seed-at08",
    )
    facade = ExpertiseOSService(
        product_graph.knowledge,
        product_graph.backend,
        product_graph.state,
        (),
    )
    revision = facade.propose_revision(
        "proposal-at08-revision",
        "operation-at08-revision",
        "session-at08",
        "codex",
        original.id,
        original.version,
        approved("revised scope"),
        NOW,
    )
    assert revision.status is ToolStatus.OK
    rejected = facade.commit_proposal(
        "proposal-at08-revision",
        "missing-grant-at08",
        "operation-at08-revision",
        {original.id: original.version},
    )
    assert rejected.status is ToolStatus.REJECTED
    assert product_graph.backend.get(original.id) == original
    product_graph.knowledge.register_decision(
        "proposal-at08-revision",
        "grant-at08-revision",
        observation(user_event_ref="host-user-at08-revision"),
        NOW + timedelta(seconds=1),
    )
    committed = facade.commit_proposal(
        "proposal-at08-revision",
        "grant-at08-revision",
        "operation-at08-revision",
        {original.id: original.version},
    )
    assert committed.status is ToolStatus.COMMITTED
    revised = product_graph.backend.get(original.id)
    assert revised is not None and revised.content == "revised scope"

    declined = facade.propose_revision(
        "proposal-at08-decline",
        "operation-at08-decline",
        "session-at08",
        "codex",
        revised.id,
        revised.version,
        approved("unapproved replacement"),
        NOW + timedelta(seconds=2),
    )
    assert declined.status is ToolStatus.OK
    assert facade.decline_proposal("proposal-at08-decline", None).status is ToolStatus.OK
    assert product_graph.backend.get(original.id) == revised
