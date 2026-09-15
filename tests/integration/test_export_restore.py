#!/usr/bin/env python3
# Purpose: Test approved C003/C004 export, validation, collision, and restore behavior.

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from expertiseos.domain.models import ApprovalReceipt, PendingOperationKind
from expertiseos.ownership import (
    BackendSnapshotSource,
    CollisionPolicy,
    CompositeSnapshotSource,
    OwnershipStatus,
    SelectionAuthority,
    SQLiteSnapshotSource,
    export_approved,
    restore_validated,
    validate_restore,
)
from expertiseos.state.sqlite import SQLiteState
from tests.backend_support import FakeBasicMemoryCli, approved, backend
from tests.fakes_reliability import FakeIdentityLookup, FakeRestoreTarget
from tests.integration.fixtures.reliability_fixtures import FIXED_NOW, approved_scope, user_event


def _receipt(knowledge_id: str) -> ApprovalReceipt:
    return ApprovalReceipt(
        "receipt-1",
        "proposal-1",
        PendingOperationKind.CREATE,
        ((knowledge_id, 1),),
        "a" * 64,
        "host:create",
        "adapter-1",
        FIXED_NOW,
    )


def test_actual_backend_and_sqlite_state_export_restore_round_trip(tmp_path: Path) -> None:
    store = backend(tmp_path, FakeBasicMemoryCli())
    record = store.create_approved(
        approved("portable approved value", "python", ("fact",), ("domain",), ("host:1",)),
        "create-1",
    )
    state = SQLiteState(tmp_path / "state.sqlite")
    state.record_receipt(_receipt(record.id))
    scope = approved_scope(record.id)
    source = CompositeSnapshotSource((BackendSnapshotSource(store), SQLiteSnapshotSource(state)))
    authority = SelectionAuthority(b"s" * 32, "adapter-1", "session-1")
    destination = tmp_path / "export"
    binding = authority.issue_export(user_event("export-event"), "export-1", scope, destination)

    result = export_approved(
        binding, scope, destination, source, authority, "0.1.0", datetime(2026, 9, 14, tzinfo=UTC)
    )

    assert result.status is OwnershipStatus.COMMITTED
    assert result.record_counts == (("knowledge", 1), ("approval_receipt", 1))
    assert "candidate" not in (destination / "manifest.json").read_text(encoding="utf-8")
    plan = validate_restore(destination, FakeIdentityLookup({}))
    assert plan.validation_errors == ()
    target = FakeRestoreTarget(False)
    restore_binding = authority.issue_restore(
        user_event("restore-event"), "restore-1", plan, CollisionPolicy.REJECT_DIVERGENT
    )
    restored = restore_validated(plan, restore_binding, authority, target)
    assert restored.status is OwnershipStatus.COMMITTED
    assert restored.restored_counts == (("knowledge", 1), ("approval_receipt", 1))
    assert [section[0] for section in target.sections] == ["knowledge", "approval_receipt"]
    state.close()


def test_divergent_collision_stops_before_mutation(tmp_path: Path) -> None:
    store = backend(tmp_path, FakeBasicMemoryCli())
    record = store.create_approved(
        approved("collision value", None, ("fact",), ("domain",), ("host:1",)), "create-1"
    )
    state = SQLiteState(tmp_path / "state.sqlite")
    state.record_receipt(_receipt(record.id))
    scope = approved_scope(record.id)
    authority = SelectionAuthority(b"s" * 32, "adapter-1", "session-1")
    destination = tmp_path / "export"
    result = export_approved(
        authority.issue_export(user_event("export-event"), "export-1", scope, destination),
        scope,
        destination,
        CompositeSnapshotSource((BackendSnapshotSource(store), SQLiteSnapshotSource(state))),
        authority,
        "0.1.0",
        FIXED_NOW,
    )
    assert result.status is OwnershipStatus.COMMITTED
    incoming = json.loads((destination / "knowledge.jsonl").read_text(encoding="utf-8"))
    digest = hashlib.sha256(
        json.dumps(incoming, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    plan = validate_restore(
        destination,
        FakeIdentityLookup({("knowledge", record.id, 1): "0" * 64, ("unused", "x", 1): digest}),
    )
    assert len(plan.collisions) == 1
    target = FakeRestoreTarget(False)
    binding = authority.issue_restore(
        user_event("restore-event"), "restore-1", plan, CollisionPolicy.REJECT_DIVERGENT
    )
    restored = restore_validated(plan, binding, authority, target)
    assert restored.status is OwnershipStatus.CONFLICT
    assert target.sections == []
    state.close()


def test_malformed_bundle_path_is_rejected(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    manifest = {
        "schema_version": 1,
        "export_id": "export-1",
        "files": [
            {
                "record_type": "knowledge",
                "path": "../outside.jsonl",
                "sha256": "0" * 64,
                "bytes": 0,
                "count": 0,
            }
        ],
    }
    (bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert validate_restore(bundle, FakeIdentityLookup({})).validation_errors == ("OwnershipError",)


def test_identical_records_are_no_op_and_rebuild_failure_is_explicit(tmp_path: Path) -> None:
    store = backend(tmp_path, FakeBasicMemoryCli())
    record = store.create_approved(
        approved("same value", None, ("fact",), ("domain",), ("host:1",)), "create-1"
    )
    state = SQLiteState(tmp_path / "state.sqlite")
    state.record_receipt(_receipt(record.id))
    scope = approved_scope(record.id)
    authority = SelectionAuthority(b"s" * 32, "adapter-1", "session-1")
    destination = tmp_path / "export"
    result = export_approved(
        authority.issue_export(user_event("export-event"), "export-1", scope, destination),
        scope,
        destination,
        CompositeSnapshotSource((BackendSnapshotSource(store), SQLiteSnapshotSource(state))),
        authority,
        "0.1.0",
        FIXED_NOW,
    )
    assert result.status is OwnershipStatus.COMMITTED
    knowledge = json.loads((destination / "knowledge.jsonl").read_text(encoding="utf-8"))
    digest = hashlib.sha256(
        json.dumps(knowledge, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    plan = validate_restore(destination, FakeIdentityLookup({("knowledge", record.id, 1): digest}))
    assert plan.identical_count == 1
    target = FakeRestoreTarget(True)
    binding = authority.issue_restore(
        user_event("restore-event"), "restore-1", plan, CollisionPolicy.REJECT_DIVERGENT
    )
    restored = restore_validated(plan, binding, authority, target)
    assert restored.status is OwnershipStatus.REPAIR_REQUIRED
    assert restored.identical_count == 1
    assert target.sections[0][0] == "approval_receipt"
    state.close()
