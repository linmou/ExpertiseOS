#!/usr/bin/env python3
# Purpose: Test normal local ownership paths do not attempt outbound network access.

from __future__ import annotations

import socket
from pathlib import Path

from expertiseos.knowledge.backend import SearchQuery
from tests.backend_support import FakeBasicMemoryCli, approved, backend


def test_local_write_read_search_with_outbound_connect_denied(
    tmp_path: Path, monkeypatch: object
) -> None:
    attempts: list[object] = []

    def deny_connect(self: socket.socket, address: object) -> None:
        attempts.append(address)
        raise AssertionError("outbound network attempted")

    monkeypatch.setattr(socket.socket, "connect", deny_connect)  # type: ignore[attr-defined]
    store = backend(tmp_path, FakeBasicMemoryCli())
    record = store.create_approved(
        approved("offline value", None, ("fact",), ("domain",), ("host:1",)), "create-1"
    )
    assert store.get(record.id) == record
    assert store.search(SearchQuery("offline", 3, None, (), (), ()))[0].knowledge_id == record.id
    assert attempts == []
