#!/usr/bin/env python3
# Purpose: Test src/expertiseos/state/sqlite.py minimal receipt persistence and replay.

from __future__ import annotations

import dataclasses
import sqlite3
from pathlib import Path

import pytest

from expertiseos.domain.errors import ReceiptConflictError
from expertiseos.domain.models import ApprovalReceipt, PendingOperationKind
from expertiseos.state.sqlite import SQLiteState
from tests.consent_support import NOW


def receipt(operation_id: str = "operation-1") -> ApprovalReceipt:
    return ApprovalReceipt(
        operation_id,
        "proposal-1",
        PendingOperationKind.CREATE,
        (("knowledge-1", 1),),
        "a" * 64,
        "host-user-event-1",
        "codex",
        NOW,
    )


def test_schema_contains_only_approved_consent_and_learning_state() -> None:
    state = SQLiteState(":memory:")
    assert state.table_names() == (
        "approval_receipts",
        "control_operations",
        "control_state",
        "deferred_activities",
        "deferred_activity_refs",
        "learner_evidence",
        "period_progress",
        "progress_events",
        "scope_exclusions",
    )
    assert all("candidate" not in name for name in state.table_names())
    state.close()


def test_exact_receipt_insert_and_replay_are_idempotent() -> None:
    state = SQLiteState(":memory:")
    value = receipt()
    assert state.record_receipt(value) == value
    assert state.record_receipt(value) == value
    assert state.get_receipt(value.operation_id) == value
    state.close()


def test_divergent_operation_id_reuse_is_rejected() -> None:
    state = SQLiteState(":memory:")
    state.record_receipt(receipt())
    with pytest.raises(ReceiptConflictError):
        state.record_receipt(dataclasses.replace(receipt(), proposal_id="different"))
    state.close()


def test_receipt_database_contains_no_candidate_payload(tmp_path: Path) -> None:
    database = tmp_path / "consent.sqlite3"
    state = SQLiteState(database)
    marker = "UNAPPROVED_MARKER_74E9"
    state.record_receipt(receipt())
    state.close()
    connection = sqlite3.connect(database)
    dump = "\n".join(connection.iterdump())
    connection.close()
    assert marker not in dump
    assert "candidate" not in dump.casefold()
