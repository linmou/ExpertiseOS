#!/usr/bin/env python3
# Purpose: Provide deterministic ownership and reliability protocol fakes for tests.

from __future__ import annotations

from collections.abc import Mapping

from expertiseos.ownership import (
    DeletionTargetResult,
    ExportScope,
    ExportSection,
    KnowledgeRef,
)


class FakeSnapshotSource:
    def __init__(self, sections: tuple[ExportSection, ...]) -> None:
        self.sections = sections
        self.calls: list[ExportScope] = []

    def snapshot(self, scope: ExportScope) -> tuple[ExportSection, ...]:
        self.calls.append(scope)
        return self.sections


class FakeIdentityLookup:
    def __init__(self, values: Mapping[tuple[str, str, int], str]) -> None:
        self.values = dict(values)

    def digest_for(self, record_type: str, identity: str, version: int) -> str | None:
        return self.values.get((record_type, identity, version))


class FakeRestoreTarget:
    def __init__(self, fail_rebuild: bool) -> None:
        self.fail_rebuild = fail_rebuild
        self.sections: list[tuple[str, tuple[Mapping[str, object], ...], str]] = []
        self.rebuild_calls = 0

    def restore_section(
        self,
        record_type: str,
        records: tuple[Mapping[str, object], ...],
        operation_id: str,
    ) -> int:
        self.sections.append((record_type, records, operation_id))
        return len(records)

    def rebuild_index(self) -> None:
        self.rebuild_calls += 1
        if self.fail_rebuild:
            raise RuntimeError("index unavailable")


class FakeLearningDeletionTarget:
    def __init__(self, fail: bool) -> None:
        self.fail = fail
        self.calls: list[tuple[tuple[KnowledgeRef, ...], bool, bool, str]] = []

    def delete_learning_scope(
        self,
        refs: tuple[KnowledgeRef, ...],
        remove_evidence_excerpts: bool,
        remove_deferred_activities: bool,
        operation_id: str,
    ) -> tuple[DeletionTargetResult, ...]:
        self.calls.append(
            (refs, remove_evidence_excerpts, remove_deferred_activities, operation_id)
        )
        if self.fail:
            raise RuntimeError("learning state unavailable")
        return (
            DeletionTargetResult("learner_evidence", True, "removed"),
            DeletionTargetResult("deferred_activity", True, "removed"),
        )


class FakeReceiptLookup:
    def __init__(self, receipts: Mapping[str, object]) -> None:
        self.receipts = dict(receipts)

    def get_receipt(self, operation_id: str) -> object | None:
        return self.receipts.get(operation_id)


class FakeReceiptReconciler:
    def __init__(self, receipt: object | Exception) -> None:
        self.receipt = receipt
        self.calls: list[str] = []

    def reconcile_receipt(self, operation_id: str) -> object:
        self.calls.append(operation_id)
        if isinstance(self.receipt, Exception):
            raise self.receipt
        return self.receipt
