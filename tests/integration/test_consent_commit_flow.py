#!/usr/bin/env python3
# Purpose: Test the real C002 proposal-to-SQLite commit path over C001's fake backend.

from __future__ import annotations

from datetime import timedelta

import pytest

from expertiseos.approval.gate import ApprovalGate
from expertiseos.domain.models import ApprovalReceipt, CommitStatus
from expertiseos.knowledge.backend import SearchQuery
from expertiseos.knowledge.service import KnowledgeService
from expertiseos.state.sqlite import SQLiteState
from tests.consent_support import NOW, approved, observation, present_create, service_bundle

pytestmark = pytest.mark.integration


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


def test_actual_proposal_grant_gate_backend_readback_and_sqlite_receipt() -> None:
    bundle = service_bundle()
    proposal_id, grant_id = present_create(bundle, "integrated approved marker")
    result = bundle.service.commit(proposal_id, grant_id, "operation-1")
    assert result.status is CommitStatus.COMMITTED
    assert result.receipt is not None
    assert result.records[0] == bundle.backend.get("knowledge-1", 1)
    assert bundle.receipts.get_receipt("operation-1") == result.receipt
    assert bundle.backend.search(SearchQuery("approved marker", 1, None, (), (), ()))[
        0
    ].knowledge_id == ("knowledge-1")


def test_unapproved_marker_never_crosses_into_backend_or_sqlite() -> None:
    bundle = service_bundle()
    marker = "UNAPPROVED_INTEGRATION_MARKER_91B2"
    proposal_id, _ = present_create(bundle, marker)
    bundle.service.decline(proposal_id, None)
    assert bundle.backend.search(SearchQuery(marker, 10, None, (), (), ())) == ()
    assert bundle.receipts.get_receipt("operation-1") is None


def test_receipt_failure_reconciles_without_duplicate_backend_version() -> None:
    bundle = service_bundle()
    service = KnowledgeService(
        bundle.backend,
        bundle.candidates,
        bundle.grants,
        ApprovalGate(),
        FailOnceReceiptStore(bundle.receipts),
        lambda: NOW + timedelta(hours=2),
    )
    service.propose_create(
        "proposal-1",
        "operation-1",
        "session-1",
        "codex",
        approved("one object"),
        NOW,
    )
    service.present("proposal-1")
    service.register_decision("proposal-1", "grant-1", observation(), NOW)
    first = service.commit("proposal-1", "grant-1", "operation-1")
    second = service.commit("proposal-1", "grant-1", "operation-1")
    assert first.status is CommitStatus.INCOMPLETE
    assert second.status is CommitStatus.COMMITTED
    assert second.records[0].version == 1
    assert bundle.backend.get_current_versions((second.records[0].id,)) == {second.records[0].id: 1}
    assert bundle.receipts.get_receipt("operation-1") == second.receipt
