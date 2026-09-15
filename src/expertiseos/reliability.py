#!/usr/bin/env python3
# Purpose: Classify commit, recovery, index repair, and degraded local search outcomes.

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from expertiseos.domain.models import ApprovalReceipt, CommitResult, CommitStatus
from expertiseos.knowledge.backend import (
    IndexState,
    KnowledgeBackend,
    RetrievalResponse,
    SearchMode,
    SearchQuery,
    SearchResult,
    StoreState,
)


class ReliabilityError(ValueError):
    """Raised when content-free recovery state is malformed."""


class OperationKind(StrEnum):
    RECEIPT_RECONCILIATION = "receipt_reconciliation"
    INDEX_REBUILD = "index_rebuild"
    RESTORE = "restore"
    DELETE = "delete"


class OperationStatus(StrEnum):
    PENDING = "pending"
    COMMITTED = "committed"
    INCOMPLETE = "incomplete"
    REPAIR_REQUIRED = "repair_required"


@dataclass(frozen=True)
class OperationRecord:
    operation_id: str
    operation_kind: OperationKind
    object_refs: tuple[tuple[str, int], ...]
    status: OperationStatus

    def __post_init__(self) -> None:
        if not self.operation_id:
            raise ReliabilityError("operation id is required")
        if any(not identity or version < 1 for identity, version in self.object_refs):
            raise ReliabilityError("operation references must contain positive versions")


@dataclass(frozen=True)
class CommitOutcome:
    status: CommitStatus
    operation_id: str
    render_saved: bool
    degraded: bool
    repair_required: bool
    error_code: str | None


@dataclass(frozen=True)
class SearchHealth:
    mode: SearchMode
    canonical_available: bool
    repair_required: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class UntrustedKnowledgeResult:
    results: tuple[SearchResult, ...]
    health: SearchHealth
    applied_limit: int


@dataclass(frozen=True)
class RecoveryResult:
    committed_operations: tuple[str, ...]
    incomplete_operations: tuple[str, ...]
    repair_required: bool
    error_codes: tuple[str, ...]


class ReceiptLookup(Protocol):
    def get_receipt(self, operation_id: str) -> ApprovalReceipt | None: ...


class ReceiptReconciler(Protocol):
    def reconcile_receipt(self, operation_id: str) -> ApprovalReceipt: ...


def classify_commit(result: CommitResult, backend: KnowledgeBackend) -> CommitOutcome:
    health = backend.health()
    committed = result.status is CommitStatus.COMMITTED and result.receipt is not None
    degraded = health.index is not IndexState.READY
    return CommitOutcome(
        result.status,
        "" if result.receipt is None else result.receipt.operation_id,
        committed,
        degraded,
        committed and degraded,
        result.error_code,
    )


def search_with_degradation(
    backend: KnowledgeBackend, query: SearchQuery
) -> UntrustedKnowledgeResult:
    results = backend.search(query)
    backend_health = backend.health()
    mode = results[0].match_mode if results else backend_health.search_mode
    index = results[0].index_state if results else backend_health.index
    health = SearchHealth(
        mode,
        backend_health.canonical_store is StoreState.READY,
        index is not IndexState.READY,
        backend_health.details,
    )
    return UntrustedKnowledgeResult(results[: query.limit], health, query.limit)


def retrieval_response(result: UntrustedKnowledgeResult) -> RetrievalResponse:
    index_state = IndexState.READY if not result.health.repair_required else IndexState.DEGRADED
    canonical = StoreState.READY if result.health.canonical_available else StoreState.UNAVAILABLE
    return RetrievalResponse(
        result.results,
        result.health.mode,
        result.health.repair_required,
        canonical,
        index_state,
        result.health.canonical_available and not result.health.repair_required,
    )


def recover_approved_state(
    operations: tuple[OperationRecord, ...],
    receipts: ReceiptLookup,
    reconciler: ReceiptReconciler,
    backend: KnowledgeBackend,
) -> RecoveryResult:
    committed: list[str] = []
    incomplete: list[str] = []
    errors: list[str] = []
    repair_required = False
    seen: set[str] = set()
    for operation in operations:
        if operation.operation_id in seen:
            raise ReliabilityError("duplicate recovery operation id")
        seen.add(operation.operation_id)
        if operation.operation_kind is OperationKind.RECEIPT_RECONCILIATION:
            try:
                receipt = receipts.get_receipt(operation.operation_id)
                if receipt is None:
                    receipt = reconciler.reconcile_receipt(operation.operation_id)
                if receipt.operation_id != operation.operation_id:
                    raise ReliabilityError("reconciled receipt identity mismatch")
                committed.append(operation.operation_id)
            except Exception as error:
                incomplete.append(operation.operation_id)
                errors.append(error.__class__.__name__)
        elif operation.operation_kind is OperationKind.INDEX_REBUILD:
            try:
                backend.rebuild_index()
                committed.append(operation.operation_id)
            except Exception as error:
                repair_required = True
                incomplete.append(operation.operation_id)
                errors.append(error.__class__.__name__)
        elif operation.status is OperationStatus.COMMITTED:
            committed.append(operation.operation_id)
        else:
            incomplete.append(operation.operation_id)
    return RecoveryResult(tuple(committed), tuple(incomplete), repair_required, tuple(errors))
