#!/usr/bin/env python3
# Purpose: Test approved retirement and enumerated idempotent deletion outcomes.

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from expertiseos.domain.models import ApprovalReceipt, PendingOperationKind
from expertiseos.knowledge.backend import IndexState, KnowledgeStatus, SearchMode, StoreState
from expertiseos.ownership import (
    DeletionScope,
    KnowledgeRef,
    OwnershipStatus,
    execute_delete,
    plan_delete,
    retire_approved,
)
from tests.backend_support import approved
from tests.fakes import DeterministicClock, DeterministicIdGenerator, FakeKnowledgeBackend
from tests.fakes_reliability import FakeLearningDeletionTarget


def _backend() -> FakeKnowledgeBackend:
    return FakeKnowledgeBackend(
        DeterministicClock(datetime(2026, 9, 14, tzinfo=UTC), timedelta(seconds=1)),
        DeterministicIdGenerator("knowledge", 1),
        StoreState.READY,
        IndexState.READY,
        SearchMode.LOCAL_INDEXED,
    )


def _receipt(kind: PendingOperationKind, ref: KnowledgeRef, operation_id: str) -> ApprovalReceipt:
    return ApprovalReceipt(
        operation_id,
        "proposal-1",
        kind,
        ((ref.knowledge_id, ref.version),),
        "a" * 64,
        "host:event",
        "adapter-1",
        datetime(2026, 9, 14, tzinfo=UTC),
    )


def test_retirement_preserves_history_and_delete_cleans_enumerated_targets() -> None:
    store = _backend()
    first = store.create_approved(
        approved("retire me", None, ("fact",), ("domain",), ("host:1",)), "create-1"
    )
    retired = retire_approved(
        _receipt(PendingOperationKind.RETIRE, KnowledgeRef(first.id, 1), "retire-1"), store
    )
    assert retired.status is KnowledgeStatus.RETIRED
    assert store.get(first.id, 1, include_retired=True) == first

    second = store.create_approved(
        approved("delete me", None, ("fact",), ("domain",), ("host:2",)), "create-2"
    )
    ref = KnowledgeRef(second.id, second.version)
    scope = DeletionScope((ref,), True, True, True, ("host backups are external",))
    plan = plan_delete(scope, _receipt(PendingOperationKind.DELETE, ref, "delete-1"))
    learning = FakeLearningDeletionTarget(False)
    result = execute_delete(plan, store, learning)
    assert result.status is OwnershipStatus.COMMITTED
    assert store.get(second.id, include_retired=True) is None
    assert result.external_limits == ("host backups are external",)
    assert {target.target for target in result.targets} == {
        f"knowledge:{second.id}",
        "learner_evidence",
        "deferred_activity",
    }


def test_partial_learning_cleanup_is_reported_incomplete() -> None:
    store = _backend()
    record = store.create_approved(
        approved("delete me", None, ("fact",), ("domain",), ("host:1",)), "create-1"
    )
    ref = KnowledgeRef(record.id, 1)
    plan = plan_delete(
        DeletionScope((ref,), True, True, True, ()),
        _receipt(PendingOperationKind.DELETE, ref, "delete-1"),
    )
    result = execute_delete(plan, store, FakeLearningDeletionTarget(True))
    assert result.status is OwnershipStatus.INCOMPLETE
    assert result.targets[-1].target == "learning_state"
