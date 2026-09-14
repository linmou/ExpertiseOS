#!/usr/bin/env python3
# Purpose: Test src/expertiseos/backends/basic_memory.py retire, delete, and version guards.

from pathlib import Path

import pytest

from expertiseos.knowledge.backend import (
    IdempotencyConflictError,
    KnowledgeStatus,
    SearchQuery,
    VersionConflictError,
)
from tests.backend_support import FakeBasicMemoryCli, approved, backend


def test_retired_record_leaves_recall_but_history_remains(tmp_path: Path) -> None:
    store = backend(tmp_path, FakeBasicMemoryCli())
    record = store.create_approved(
        approved("retire marker", None, ("fact",), ("domain",), ("event:1",)),
        "create-retire",
    )
    retired = store.retire(record.id, 1, "retire")
    assert retired.status is KnowledgeStatus.RETIRED
    assert store.get(record.id) is None
    assert store.get(record.id, 1, True) == record
    assert store.get(record.id, 2, True) == retired
    assert store.search(SearchQuery("retire marker", 5, None, (), (), ())) == ()


def test_delete_checks_version_removes_all_notes_and_replays(tmp_path: Path) -> None:
    cli = FakeBasicMemoryCli()
    store = backend(tmp_path, cli)
    record = store.create_approved(
        approved("delete marker", None, ("fact",), ("domain",), ("event:1",)),
        "create-delete",
    )
    updated = store.update_approved(
        record.id,
        1,
        approved("delete marker v2", None, ("fact",), ("domain",), ("event:2",)),
        "update-delete",
    )
    with pytest.raises(VersionConflictError):
        store.delete(record.id, 1, "delete-stale")
    deleted = store.delete(record.id, updated.version, "delete-current")
    assert deleted.deleted_versions == 2
    assert store.delete(record.id, updated.version, "delete-current") == deleted
    assert store.get(record.id, 1, True) is None
    assert store.search(SearchQuery("delete", 5, None, (), (), ())) == ()
    assert not cli.notes
    with pytest.raises(IdempotencyConflictError):
        store.delete("different", 1, "delete-current")
