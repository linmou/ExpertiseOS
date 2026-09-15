#!/usr/bin/env python3
# Purpose: Test src/expertiseos/backends/basic_memory.py relationship and conflict mapping.

from pathlib import Path

import pytest

from expertiseos.knowledge.backend import IdempotencyConflictError, RelationshipInput, SearchQuery
from tests.backend_support import FakeBasicMemoryCli, approved, backend


def test_relationships_and_conflicts_round_trip_without_consolidation(tmp_path: Path) -> None:
    store = backend(tmp_path, FakeBasicMemoryCli())
    source = store.create_approved(
        approved("retry is safe", "idempotent", ("procedure",), ("domain",), ("event:1",)),
        "create-source",
    )
    target = store.create_approved(
        approved("retry is unsafe", "side-effecting", ("boundary",), ("domain",), ("event:2",)),
        "create-target",
    )
    relation = RelationshipInput(
        source.id, 1, target.id, 1, "contradicts", "different conditions", "event:3"
    )
    updated = store.set_relationships((relation,), {source.id: 1, target.id: 1}, "relate-1")
    assert store.set_relationships((relation,), {source.id: 1, target.id: 1}, "relate-1") == updated
    result = store.search(SearchQuery("retry", 5, None, (), (), ()))
    by_id = {item.knowledge_id: item for item in result}
    assert by_id[source.id].relationships == (relation,)
    assert by_id[source.id].conflicts == (target.id,)
    assert target.id in by_id
    with pytest.raises(IdempotencyConflictError):
        store.set_relationships((), {source.id: 1}, "relate-1")
