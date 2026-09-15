#!/usr/bin/env python3
# Purpose: Test delegated authorization and receipt completion without downstream writes.

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from expertiseos.approval.gate import ApprovalGate
from expertiseos.domain.errors import (
    ApprovalRejectedError,
    ReceiptConflictError,
    StaleVersionError,
)
from expertiseos.domain.models import (
    ApprovalReceipt,
    AuthorizedOperation,
    CandidateState,
    CommitStatus,
    ControlChangeOperation,
    DeleteOperation,
    LearningEvidenceOperation,
    PendingOperationKind,
)
from expertiseos.hosts.contract import DecisionAction, DecisionObservation, DecisionRejection
from expertiseos.knowledge.service import KnowledgeService
from expertiseos.state.sqlite import SQLiteState
from tests.consent_support import NOW, observation, service_bundle


class FailOnceReceiptStore:
    def __init__(self, delegate: SQLiteState) -> None:
        self.delegate = delegate
        self.failed = False

    def get_receipt(self, operation_id: str) -> ApprovalReceipt | None:
        return self.delegate.get_receipt(operation_id)

    def record_receipt(self, receipt: ApprovalReceipt) -> ApprovalReceipt:
        if not self.failed:
            self.failed = True
            raise OSError("injected receipt failure")
        return self.delegate.record_receipt(receipt)


def present_and_grant(
    service: KnowledgeService,
    proposal_id: str,
    grant_id: str,
    user_event_ref: str,
) -> None:
    service.present(proposal_id)
    service.register_decision(
        proposal_id,
        grant_id,
        observation(user_event_ref=user_event_ref),
        NOW,
    )


@pytest.mark.parametrize(
    ("method_name", "kind", "payload_type"),
    (
        (
            "propose_learning_evidence",
            PendingOperationKind.LEARNING_EVIDENCE,
            LearningEvidenceOperation,
        ),
        (
            "propose_control_change",
            PendingOperationKind.CONTROL_CHANGE,
            ControlChangeOperation,
        ),
        ("propose_delete", PendingOperationKind.DELETE, DeleteOperation),
    ),
)
def test_named_delegated_proposals_prepare_without_commit_or_backend_write(
    method_name: str,
    kind: PendingOperationKind,
    payload_type: type[object],
) -> None:
    bundle = service_bundle()
    method = getattr(bundle.service, method_name)
    proposal = method(
        "proposal-1",
        "operation-1",
        "session-1",
        "codex",
        {"exact": "displayed value"},
        {"state-1": 1},
        NOW,
    )
    present_and_grant(bundle.service, proposal.proposal_id, "grant-1", "event-1")

    authorization = bundle.service.prepare_delegated_commit(
        proposal.proposal_id,
        "grant-1",
        proposal.operation_id,
        {"state-1": 1},
    )

    assert authorization.kind is kind
    assert isinstance(authorization.payload, payload_type)
    assert authorization.existing_receipt is None
    assert bundle.receipts.get_receipt(proposal.operation_id) is None
    assert bundle.grants.get("grant-1").consumed_at is None  # type: ignore[union-attr]
    assert bundle.candidates.get(proposal.proposal_id).state is (  # type: ignore[union-attr]
        CandidateState.AWAITING_DECISION
    )
    assert bundle.service.commit(proposal.proposal_id, "grant-1", proposal.operation_id).status is (
        CommitStatus.REJECTED
    )
    assert bundle.backend.get_current_versions(()) == {}


def test_prepare_rejects_mutated_payload_stale_version_and_wrong_operation() -> None:
    bundle = service_bundle()
    value = {"criterion": "before"}
    proposal = bundle.service.propose_learning_evidence(
        "proposal-1",
        "operation-1",
        "session-1",
        "codex",
        value,
        {"knowledge-1": 2},
        NOW,
    )
    present_and_grant(bundle.service, proposal.proposal_id, "grant-1", "event-1")

    with pytest.raises(ApprovalRejectedError, match="operation_id"):
        bundle.service.prepare_delegated_commit(
            proposal.proposal_id, "grant-1", "wrong-operation", {"knowledge-1": 2}
        )
    with pytest.raises(StaleVersionError):
        bundle.service.prepare_delegated_commit(
            proposal.proposal_id, "grant-1", proposal.operation_id, {"knowledge-1": 3}
        )
    value["criterion"] = "after"
    with pytest.raises(ApprovalRejectedError, match="changed"):
        bundle.service.prepare_delegated_commit(
            proposal.proposal_id, "grant-1", proposal.operation_id, {"knowledge-1": 2}
        )
    assert bundle.receipts.get_receipt(proposal.operation_id) is None


def test_prepare_rejects_cross_session_adapter_grant_and_reused_user_event() -> None:
    bundle = service_bundle()
    first = bundle.service.propose_control_change(
        "first", "operation-first", "session-a", "codex", {"enabled": False}, {}, NOW
    )
    second = bundle.service.propose_delete(
        "second", "operation-second", "session-b", "claude", {"scope": "all"}, {}, NOW
    )
    present_and_grant(bundle.service, first.proposal_id, "grant-first", "event-1")
    bundle.service.present(second.proposal_id)
    with pytest.raises(ApprovalRejectedError, match="origin"):
        bundle.service.prepare_delegated_commit(
            second.proposal_id, "grant-first", second.operation_id, {}
        )

    third = bundle.service.propose_delete(
        "third", "operation-third", "session-a", "codex", {"scope": "one"}, {}, NOW
    )
    bundle.service.present(third.proposal_id)
    with pytest.raises(ApprovalRejectedError, match="already granted"):
        bundle.service.register_decision(
            third.proposal_id,
            "grant-third",
            observation(user_event_ref="event-1"),
            NOW,
        )
    unmatched = DecisionObservation(
        False,
        DecisionAction.SAVE,
        "event-2",
        DecisionRejection.NOT_USER_INPUT,
    )
    with pytest.raises(ApprovalRejectedError, match="actual matching"):
        bundle.service.register_decision(third.proposal_id, "grant-unmatched", unmatched, NOW)


def test_completion_rechecks_every_authorization_binding() -> None:
    bundle = service_bundle()
    proposal = bundle.service.propose_control_change(
        "proposal-1",
        "operation-1",
        "session-1",
        "codex",
        {"enabled": False},
        {"control-state": 1},
        NOW,
    )
    present_and_grant(bundle.service, proposal.proposal_id, "grant-1", "event-1")
    authorization = bundle.service.prepare_delegated_commit(
        proposal.proposal_id, "grant-1", proposal.operation_id, {"control-state": 1}
    )
    changed = (
        replace(authorization, operation_id="other-operation"),
        replace(authorization, session_id="other-session"),
        replace(authorization, adapter_id="other-adapter"),
        replace(authorization, content_digest="b" * 64),
        replace(authorization, expected_versions=(("control-state", 2),)),
        replace(authorization, payload=ControlChangeOperation({"enabled": True})),
    )
    for forged in changed:
        with pytest.raises(ApprovalRejectedError):
            bundle.service.complete_delegated_commit(forged, (("control-state", 2),))
    assert bundle.receipts.get_receipt(proposal.operation_id) is None


def test_completion_requires_preparation_by_same_service_instance() -> None:
    bundle = service_bundle()
    proposal = bundle.service.propose_control_change(
        "proposal-1", "operation-1", "session-1", "codex", {"enabled": False}, {}, NOW
    )
    present_and_grant(bundle.service, proposal.proposal_id, "grant-1", "event-1")
    assert isinstance(proposal.payload, ControlChangeOperation)
    forged = AuthorizedOperation(
        "grant-1",
        proposal.proposal_id,
        proposal.operation_id,
        proposal.session_id,
        proposal.adapter_id,
        proposal.kind,
        proposal.payload,
        proposal.content_digest,
        proposal.expected_versions,
        "event-1",
        None,
    )
    with pytest.raises(ApprovalRejectedError, match="not prepared"):
        bundle.service.complete_delegated_commit(forged, (("control-state", 2),))
    assert bundle.receipts.get_receipt(proposal.operation_id) is None


def test_completion_records_then_consumes_and_exact_replay_skips_backend_readback() -> None:
    bundle = service_bundle()
    proposal = bundle.service.propose_delete(
        "proposal-1",
        "operation-1",
        "session-1",
        "codex",
        {"object_refs": (("knowledge-1", 4),)},
        {"knowledge-1": 4},
        NOW,
    )
    present_and_grant(bundle.service, proposal.proposal_id, "grant-1", "event-1")
    authorization = bundle.service.prepare_delegated_commit(
        proposal.proposal_id, "grant-1", proposal.operation_id, {"knowledge-1": 4}
    )
    receipt = bundle.service.complete_delegated_commit(authorization, (("knowledge-1", 4),))

    assert receipt.operation_kind is PendingOperationKind.DELETE
    assert bundle.grants.get("grant-1").consumed_at is not None  # type: ignore[union-attr]
    assert bundle.candidates.get(proposal.proposal_id).state is (  # type: ignore[union-attr]
        CandidateState.APPROVED
    )
    replay = bundle.service.prepare_delegated_commit(
        proposal.proposal_id, "grant-1", proposal.operation_id, {}
    )
    assert replay.existing_receipt == receipt
    assert bundle.service.complete_delegated_commit(replay, (("knowledge-1", 4),)) == receipt
    divergent_replay = bundle.service.prepare_delegated_commit(
        proposal.proposal_id, "grant-1", proposal.operation_id, {}
    )
    with pytest.raises(ReceiptConflictError, match="different affected"):
        bundle.service.complete_delegated_commit(divergent_replay, (("knowledge-1", 5),))


def test_receipt_failure_keeps_grant_retryable_with_same_operation_id() -> None:
    base = service_bundle()
    service = KnowledgeService(
        base.backend,
        base.candidates,
        base.grants,
        ApprovalGate(),
        FailOnceReceiptStore(base.receipts),
        lambda: NOW + timedelta(hours=1),
    )
    proposal = service.propose_learning_evidence(
        "proposal-1",
        "operation-1",
        "session-1",
        "codex",
        {"evidence_id": "evidence-1"},
        {"knowledge-1": 1},
        NOW,
    )
    present_and_grant(service, proposal.proposal_id, "grant-1", "event-1")
    authorization = service.prepare_delegated_commit(
        proposal.proposal_id, "grant-1", proposal.operation_id, {"knowledge-1": 1}
    )
    with pytest.raises(OSError, match="receipt failure"):
        service.complete_delegated_commit(authorization, (("evidence-1", 1),))
    assert base.receipts.get_receipt(proposal.operation_id) is None
    assert base.grants.get("grant-1").consumed_at is None  # type: ignore[union-attr]
    assert base.candidates.get(proposal.proposal_id).state is (  # type: ignore[union-attr]
        CandidateState.AWAITING_DECISION
    )

    receipt = service.complete_delegated_commit(authorization, (("evidence-1", 1),))
    assert receipt == base.receipts.get_receipt(proposal.operation_id)


def test_divergent_operation_id_reuse_rejects_other_proposal() -> None:
    bundle = service_bundle()
    first = bundle.service.propose_control_change(
        "first", "shared-operation", "session-1", "codex", {"enabled": False}, {}, NOW
    )
    present_and_grant(bundle.service, first.proposal_id, "grant-first", "event-first")
    authorization = bundle.service.prepare_delegated_commit(
        first.proposal_id, "grant-first", first.operation_id, {}
    )
    second = bundle.service.propose_control_change(
        "second", "shared-operation", "session-1", "codex", {"enabled": True}, {}, NOW
    )
    present_and_grant(bundle.service, second.proposal_id, "grant-second", "event-second")
    with pytest.raises(ReceiptConflictError, match="different authorization"):
        bundle.service.prepare_delegated_commit(
            second.proposal_id, "grant-second", second.operation_id, {}
        )

    bundle.service.complete_delegated_commit(authorization, (("control-state", 2),))

    third = bundle.service.propose_control_change(
        "third", "shared-operation", "session-1", "codex", {"enabled": True}, {}, NOW
    )
    present_and_grant(bundle.service, third.proposal_id, "grant-third", "event-third")
    with pytest.raises(ReceiptConflictError, match="receipt does not match"):
        bundle.service.prepare_delegated_commit(
            third.proposal_id, "grant-third", third.operation_id, {}
        )
