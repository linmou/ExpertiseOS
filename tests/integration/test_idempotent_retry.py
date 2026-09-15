#!/usr/bin/env python3
# Purpose: Test operation-id-only receipt reconciliation across retries.

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from expertiseos.domain.models import ApprovalReceipt, PendingOperationKind
from expertiseos.knowledge.backend import IndexState, SearchMode, StoreState
from expertiseos.reliability import (
    OperationKind,
    OperationRecord,
    OperationStatus,
    recover_approved_state,
)
from tests.fakes import DeterministicClock, DeterministicIdGenerator, FakeKnowledgeBackend


class _Receipts:
    def __init__(self) -> None:
        self.value: ApprovalReceipt | None = None

    def get_receipt(self, operation_id: str) -> ApprovalReceipt | None:
        return self.value


class _Reconciler:
    def __init__(self, receipts: _Receipts) -> None:
        self.receipts = receipts
        self.calls = 0

    def reconcile_receipt(self, operation_id: str) -> ApprovalReceipt:
        self.calls += 1
        receipt = ApprovalReceipt(
            operation_id,
            "proposal-1",
            PendingOperationKind.CREATE,
            (("knowledge-1", 1),),
            "a" * 64,
            "host:event",
            "adapter-1",
            datetime(2026, 9, 14, tzinfo=UTC),
        )
        self.receipts.value = receipt
        return receipt


def test_retry_reconciles_one_receipt_by_operation_id() -> None:
    backend = FakeKnowledgeBackend(
        DeterministicClock(datetime(2026, 9, 14, tzinfo=UTC), timedelta(seconds=1)),
        DeterministicIdGenerator("knowledge", 1),
        StoreState.READY,
        IndexState.READY,
        SearchMode.LOCAL_INDEXED,
    )
    operation = OperationRecord(
        "operation-1",
        OperationKind.RECEIPT_RECONCILIATION,
        (("knowledge-1", 1),),
        OperationStatus.PENDING,
    )
    receipts = _Receipts()
    reconciler = _Reconciler(receipts)
    first = recover_approved_state((operation,), receipts, reconciler, backend)
    second = recover_approved_state((operation,), receipts, reconciler, backend)
    assert first.committed_operations == second.committed_operations == ("operation-1",)
    assert reconciler.calls == 1
