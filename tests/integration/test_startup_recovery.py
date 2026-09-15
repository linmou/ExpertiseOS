#!/usr/bin/env python3
# Purpose: Test startup recovery permits content-free approved operation kinds only.

from __future__ import annotations

from dataclasses import fields

from expertiseos.reliability import OperationKind, OperationRecord, OperationStatus


def test_recovery_record_contains_references_not_semantic_payloads() -> None:
    names = {field.name for field in fields(OperationRecord)}
    assert names == {"operation_id", "operation_kind", "object_refs", "status"}
    assert {kind.value for kind in OperationKind} == {
        "receipt_reconciliation",
        "index_rebuild",
        "restore",
        "delete",
    }
    record = OperationRecord("operation-1", OperationKind.RESTORE, (), OperationStatus.PENDING)
    assert "content" not in repr(record)
