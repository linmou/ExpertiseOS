#!/usr/bin/env python3
# Purpose: Test src/expertiseos/backends/basic_memory.py exact approved Basic Memory round trips.

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from expertiseos.backends.basic_memory import (
    BackendUnavailableError,
    BasicMemoryBackend,
    subprocess_cli_runner,
)
from expertiseos.knowledge.backend import (
    IdempotencyConflictError,
    RelationshipInput,
    SearchQuery,
    VersionConflictError,
)
from tests.backend_support import FakeBasicMemoryCli, approved, backend
from tests.fakes import DeterministicClock
from tests.integration.test_backend_feasibility import (
    basic_memory_binary,
    configure_project,
    isolated_environment,
)


def test_exact_create_update_history_versions_and_replay(tmp_path: Path) -> None:
    cli = FakeBasicMemoryCli()
    store = backend(tmp_path, cli)
    first_value = approved("first", "python", ("procedure",), ("domain",), ("event:1",))
    first = store.create_approved(first_value, "create-1")
    assert store.create_approved(first_value, "create-1") == first
    second_value = approved("second", "python", ("boundary",), ("domain",), ("event:2",))
    second = store.update_approved(first.id, 1, second_value, "update-1")
    assert second.id == first.id
    assert second.version == 2
    assert store.get(first.id, 1, True) == first
    assert store.get(first.id) == second
    assert store.get_current_versions((first.id, "missing")) == {first.id: 2}
    with pytest.raises(IdempotencyConflictError):
        store.create_approved(second_value, "create-1")
    with pytest.raises(VersionConflictError):
        store.update_approved(first.id, 1, second_value, "update-2")


def test_restart_preserves_versions_and_operation_replay(tmp_path: Path) -> None:
    cli = FakeBasicMemoryCli()
    store = backend(tmp_path, cli)
    value = approved("restart value", None, ("fact",), ("domain",), ("event:1",))
    created = store.create_approved(value, "restart-create")

    restarted = backend(tmp_path, cli)

    assert restarted.get(created.id, 1, True) == created
    assert restarted.create_approved(value, "restart-create") == created
    assert len(cli.notes) == 1


def test_malformed_mapping_state_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "backend-state.json").write_text(
        json.dumps({"schema": 1, "records": {}}), encoding="utf-8"
    )

    with pytest.raises(BackendUnavailableError, match="unsupported schema"):
        backend(tmp_path, FakeBasicMemoryCli())


@pytest.mark.external
@pytest.mark.integration
def test_real_basic_memory_public_cli_round_trip(tmp_path: Path) -> None:
    binary = basic_memory_binary()
    environment = isolated_environment(tmp_path)
    configure_project(binary, environment, tmp_path)
    clock = DeterministicClock(datetime(2026, 9, 14, tzinfo=UTC), timedelta(seconds=1))
    store = BasicMemoryBackend(
        binary,
        "g0",
        Path(environment["BASIC_MEMORY_CONFIG_DIR"]),
        Path(environment["BASIC_MEMORY_HOME"]),
        tmp_path / "adapter-state.json",
        clock,
        subprocess_cli_runner(30.0),
    )
    value = approved("public API round trip", None, ("fact",), ("domain",), ("event:real",))
    record = store.create_approved(value, "real-create")
    assert store.get(record.id, 1, True) == record
    target = store.create_approved(
        approved("public API target", None, ("fact",), ("domain",), ("event:target",)),
        "real-target",
    )
    relationship = RelationshipInput(
        record.id, 1, target.id, 1, "supports", "public relation", "event:relation"
    )
    related = store.set_relationships(
        (relationship,), {record.id: 1, target.id: 1}, "real-relation"
    )[0]
    result = store.search(SearchQuery("public API round trip", 5, None, (), (), ()))
    assert result[0].knowledge_id == record.id
    assert result[0].relationships == (relationship,)
    assert store.rebuild_index().indexed_records == 2
    assert store.delete(record.id, related.version, "real-delete").deleted_versions == 2
    assert store.get(record.id, 1, True) is None
    assert any(command[:2] == ("tool", "write-note") for command in store.command_log)
    assert any(command[:2] == ("tool", "read-note") for command in store.command_log)
    assert any(command[:2] == ("tool", "search-notes") for command in store.command_log)
    assert any(command[:2] == ("tool", "delete-note") for command in store.command_log)
    assert any(command[:1] == ("reindex",) for command in store.command_log)
