#!/usr/bin/env python3
# Purpose: Test commit classification, recovery, retry, and degraded search behavior.

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from expertiseos.domain.models import (
    ApprovalReceipt,
    CommitResult,
    CommitStatus,
    PendingOperationKind,
)
from expertiseos.knowledge.backend import IndexState, SearchMode, SearchQuery, StoreState
from expertiseos.reliability import (
    OperationKind,
    OperationRecord,
    OperationStatus,
    ReliabilityError,
    classify_commit,
    recover_approved_state,
    search_with_degradation,
)
from tests.fakes import DeterministicClock, DeterministicIdGenerator, FakeKnowledgeBackend


def _backend(index: IndexState = IndexState.READY) -> FakeKnowledgeBackend:
    return FakeKnowledgeBackend(
        DeterministicClock(datetime(2026, 9, 14, tzinfo=UTC), timedelta(seconds=1)),
        DeterministicIdGenerator("knowledge", 1),
        StoreState.READY,
        index,
        SearchMode.KEYWORD if index is not IndexState.READY else SearchMode.LOCAL_INDEXED,
    )


def _receipt(operation_id: str) -> ApprovalReceipt:
    return ApprovalReceipt(
        operation_id,
        "proposal-1",
        PendingOperationKind.CREATE,
        (("knowledge-1", 1),),
        "a" * 64,
        "host:event-1",
        "adapter-1",
        datetime(2026, 9, 14, tzinfo=UTC),
    )


def test_only_canonical_committed_with_receipt_renders_saved() -> None:
    backend = _backend()
    for status in CommitStatus:
        receipt = _receipt("operation-1") if status is CommitStatus.COMMITTED else None
        outcome = classify_commit(CommitResult(status, (), receipt, None), backend)
        assert outcome.render_saved is (status is CommitStatus.COMMITTED)


def test_committed_write_with_bad_index_requires_repair() -> None:
    outcome = classify_commit(
        CommitResult(CommitStatus.COMMITTED, (), _receipt("operation-1"), None),
        _backend(IndexState.DEGRADED),
    )
    assert outcome.render_saved
    assert outcome.degraded
    assert outcome.repair_required


def test_recovery_rejects_duplicate_operation_identity() -> None:
    operation = OperationRecord(
        "operation-1", OperationKind.DELETE, (("knowledge-1", 1),), OperationStatus.PENDING
    )
    with pytest.raises(ReliabilityError, match="duplicate"):
        recover_approved_state((operation, operation), object(), object(), _backend())  # type: ignore[arg-type]


def test_keyword_degradation_is_explicit_and_bounded() -> None:
    backend = _backend(IndexState.DEGRADED)
    result = search_with_degradation(backend, SearchQuery("missing", 3, None, (), (), ()))
    assert result.results == ()
    assert result.applied_limit == 3
    assert result.health.mode is SearchMode.KEYWORD
    assert result.health.repair_required
