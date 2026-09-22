#!/usr/bin/env python3
# Purpose: Test src/expertiseos/knowledge/service.py exact commits and interrupted retries.

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from expertiseos.approval.gate import ApprovalGate
from expertiseos.domain.models import ApprovalReceipt, CommitStatus, CreateOperation
from expertiseos.hosts.contract import DecisionAction
from expertiseos.knowledge.backend import ApprovedKnowledgeInput, KnowledgeRecord
from expertiseos.knowledge.service import KnowledgeService
from expertiseos.state.sqlite import SQLiteState
from tests.consent_support import (
    NOW,
    approved,
    fake_backend,
    observation,
    present_create,
    service_bundle,
)
from tests.fakes import FakeKnowledgeBackend


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


class AfterWriteTimeoutBackend(FakeKnowledgeBackend):
    def __init__(self, delegate: FakeKnowledgeBackend) -> None:
        self.__dict__.update(delegate.__dict__)
        self.timed_out = False

    def create_approved(self, value: ApprovedKnowledgeInput, operation_id: str) -> KnowledgeRecord:
        record = super().create_approved(value, operation_id)
        if not self.timed_out:
            self.timed_out = True
            raise TimeoutError("injected after-write timeout")
        return record


class ConsistentlyTamperingBackend(FakeKnowledgeBackend):
    def __init__(self, delegate: FakeKnowledgeBackend) -> None:
        self.__dict__.update(delegate.__dict__)

    def create_approved(self, value: ApprovedKnowledgeInput, operation_id: str) -> KnowledgeRecord:
        record = super().create_approved(value, operation_id)
        tampered = replace(record, content="backend-tampered-content")
        self._history[record.id][-1] = tampered
        return tampered


def test_exact_create_read_back_receipt_and_post_success_replay() -> None:
    bundle = service_bundle()
    proposal_id, grant_id = present_create(bundle, "save this")
    result = bundle.service.commit(proposal_id, grant_id, "operation-1")
    assert result.status is CommitStatus.COMMITTED
    assert result.records[0].content == "save this"
    assert not hasattr(result.records[0], "learner_state")
    assert result.receipt is not None
    assert result.receipt.object_ids_versions == (("knowledge-1", 1),)
    assert bundle.candidates.get(proposal_id).state.value == "approved"  # type: ignore[union-attr]
    assert bundle.grants.get(grant_id).consumed_at is not None  # type: ignore[union-attr]
    assert bundle.service.commit(proposal_id, grant_id, "operation-1") == result


def test_direct_create_uses_one_actual_decision_and_exact_commit() -> None:
    bundle = service_bundle()
    proposal, grant = bundle.service.propose_direct_create(
        "proposal-direct",
        "operation-direct",
        "session-1",
        "codex",
        approved("direct approved content"),
        observation(DecisionAction.SAVE),
        "grant-direct",
        NOW,
    )
    result = bundle.service.commit(proposal.proposal_id, grant.grant_id, proposal.operation_id)
    assert result.status is CommitStatus.COMMITTED
    assert result.records[0].content == "direct approved content"


def test_displayed_edit_invalidates_old_grant_and_commits_new_digest() -> None:
    bundle = service_bundle()
    proposal_id, grant_id = present_create(bundle, "before")
    updated = bundle.service.revise_displayed_proposal(
        proposal_id, CreateOperation(approved("after"))
    )
    assert bundle.grants.get(grant_id) is None
    assert bundle.service.commit(proposal_id, grant_id, "operation-1").status is (
        CommitStatus.REJECTED
    )
    bundle.service.register_decision(
        proposal_id,
        "grant-new",
        observation(user_event_ref="host-user-event-edit"),
        NOW + timedelta(minutes=2),
    )
    result = bundle.service.commit(proposal_id, "grant-new", "operation-1")
    assert result.status is CommitStatus.COMMITTED
    assert result.records[0].content == "after"
    assert result.receipt is not None and result.receipt.content_digest == updated.content_digest


def test_receipt_failure_retries_without_duplicate_create() -> None:
    base = service_bundle()
    receipt_store = FailOnceReceiptStore(base.receipts)
    service = KnowledgeService(
        base.backend,
        base.candidates,
        base.grants,
        ApprovalGate(),
        receipt_store,
        lambda: NOW + timedelta(hours=2),
    )
    base = replace(base, service=service)
    proposal_id, grant_id = present_create(base, "one object")
    first = service.commit(proposal_id, grant_id, "operation-1")
    assert first.status is CommitStatus.INCOMPLETE
    second = service.commit(proposal_id, grant_id, "operation-1")
    assert second.status is CommitStatus.COMMITTED
    assert second.receipt is not None
    assert base.backend.get_current_versions(("knowledge-1",)) == {"knowledge-1": 1}


def test_after_write_timeout_replays_same_operation_id() -> None:
    backend = AfterWriteTimeoutBackend(fake_backend())
    bundle = service_bundle(backend)
    proposal_id, grant_id = present_create(bundle, "timeout content")
    assert bundle.service.commit(proposal_id, grant_id, "operation-1").status is (
        CommitStatus.FAILED
    )
    retried = bundle.service.commit(proposal_id, grant_id, "operation-1")
    assert retried.status is CommitStatus.COMMITTED
    assert backend.get_current_versions(("knowledge-1",)) == {"knowledge-1": 1}


def test_consistently_tampered_backend_result_fails_before_receipt() -> None:
    bundle = service_bundle(ConsistentlyTamperingBackend(fake_backend()))
    proposal_id, grant_id = present_create(bundle, "approved content")
    result = bundle.service.commit(proposal_id, grant_id, "operation-1")
    assert result.status is CommitStatus.FAILED
    assert result.error_code == "ReadBackMismatchError"
    assert bundle.receipts.get_receipt("operation-1") is None
