#!/usr/bin/env python3
# Purpose: Test src/expertiseos/backends/basic_memory.py index health and rebuild behavior.

from pathlib import Path

import pytest

from expertiseos.backends.basic_memory import BackendUnavailableError
from expertiseos.knowledge.backend import IndexState, SearchQuery
from tests.backend_support import FakeBasicMemoryCli, approved, backend


def test_write_ack_failure_reconciles_canonical_note_and_degrades_index(tmp_path: Path) -> None:
    cli = FakeBasicMemoryCli()
    cli.fail_write_after_store = True
    store = backend(tmp_path, cli)
    record = store.create_approved(
        approved("canonical survived", None, ("fact",), ("domain",), ("event:1",)),
        "create-reconcile",
    )
    assert store.get(record.id, 1, True) == record
    assert store.health().index is IndexState.DEGRADED


def test_rebuild_is_idempotent_and_indexes_active_canonical_records(tmp_path: Path) -> None:
    cli = FakeBasicMemoryCli()
    store = backend(tmp_path, cli)
    active = store.create_approved(
        approved("active token", None, ("fact",), ("domain",), ("event:1",)),
        "create-active",
    )
    retired = store.create_approved(
        approved("retired token", None, ("fact",), ("domain",), ("event:2",)),
        "create-retired",
    )
    store.retire(retired.id, 1, "retire")
    first = store.rebuild_index()
    second = store.rebuild_index()
    assert first == second
    assert first.indexed_records == 1
    assert store.search(SearchQuery("active", 5, None, (), (), ()))[0].knowledge_id == active.id


def test_failed_rebuild_reports_unavailable_index_without_losing_canonical(tmp_path: Path) -> None:
    cli = FakeBasicMemoryCli()
    store = backend(tmp_path, cli)
    record = store.create_approved(
        approved("still canonical", None, ("fact",), ("domain",), ("event:1",)),
        "create-canonical",
    )
    cli.fail_reindex = True
    with pytest.raises(BackendUnavailableError):
        store.rebuild_index()
    assert store.get(record.id, 1, True) == record
    assert store.health().index is IndexState.UNAVAILABLE
