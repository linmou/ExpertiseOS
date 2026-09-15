#!/usr/bin/env python3
# Purpose: Test src/expertiseos/backends/basic_memory.py provenance round-trip and availability.

from pathlib import Path

from expertiseos.knowledge.backend import SearchQuery
from tests.backend_support import FakeBasicMemoryCli, approved, backend


def test_provenance_round_trips_and_unavailable_source_is_not_replaced(tmp_path: Path) -> None:
    store = backend(tmp_path, FakeBasicMemoryCli())
    refs = ("host_event:codex:session-1:event-1", "unavailable:file:/deleted/source.md")
    record = store.create_approved(
        approved("source-sensitive claim", None, ("fact",), ("domain",), refs),
        "create-provenance",
    )
    assert store.get(record.id, 1, True) == record
    result = store.search(SearchQuery("source-sensitive", 2, None, (), (), ()))[0]
    assert result.source_refs == refs
    assert result.provenance_available is False
    assert all("generated" not in ref for ref in result.source_refs)
