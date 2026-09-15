#!/usr/bin/env python3
# Purpose: Test src/expertiseos/backends/basic_memory.py local keyword degradation and offline path.

from pathlib import Path

from expertiseos.knowledge.backend import IndexState, SearchMode, SearchQuery
from tests.backend_support import FakeBasicMemoryCli, approved, backend


def test_index_failure_uses_bounded_local_keyword_fallback(tmp_path: Path) -> None:
    cli = FakeBasicMemoryCli()
    store = backend(tmp_path, cli)
    expected = store.create_approved(
        approved("bounded needle-query-7c91 token", "python", ("fact",), ("domain",), ("event:1",)),
        "operation-1",
    )
    cli.fail_search = True
    results = store.search(SearchQuery("needle-query-7c91", 1, "python", (), (), ()))
    assert [item.knowledge_id for item in results] == [expected.id]
    assert results[0].match_mode is SearchMode.KEYWORD
    assert results[0].index_state is IndexState.DEGRADED
    assert store.health().index is IndexState.DEGRADED
    assert "needle-query-7c91" not in (tmp_path / "backend-state.json").read_text(encoding="utf-8")


def test_network_disabled_configuration_never_adds_cloud_or_vector_flags(tmp_path: Path) -> None:
    cli = FakeBasicMemoryCli()
    store = backend(tmp_path, cli)
    store.create_approved(
        approved("offline retrieval", None, ("fact",), ("domain",), ("event:1",)),
        "create-offline",
    )
    store.search(SearchQuery("offline", 2, None, (), (), ()))
    flattened = {argument for command in cli.commands for argument in command}
    assert "--local" in flattened
    assert "--cloud" not in flattened
    assert "--vector" not in flattened
    assert "--hybrid" not in flattened
