#!/usr/bin/env python3
# Purpose: Test public contract imports and deterministic fakes used by downstream components.

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

import pytest

from expertiseos.hosts.contract import HostAdapter
from expertiseos.knowledge.backend import (
    ApprovedKnowledgeInput,
    IndexState,
    KnowledgeBackend,
    SearchMode,
    StoreState,
)
from tests.fakes import (
    DeterministicClock,
    DeterministicIdGenerator,
    FakeHostAdapter,
    FakeKnowledgeBackend,
)

pytestmark = pytest.mark.integration


def test_downstream_can_use_contracts_without_live_dependencies() -> None:
    host = FakeHostAdapter("test", "session", ())
    backend = FakeKnowledgeBackend(
        DeterministicClock(datetime(2026, 9, 14, tzinfo=UTC), timedelta(seconds=1)),
        DeterministicIdGenerator("knowledge", 1),
        StoreState.READY,
        IndexState.READY,
        SearchMode.KEYWORD,
    )
    assert isinstance(host, HostAdapter)
    assert isinstance(backend, KnowledgeBackend)
    content = "approved fixture"
    value = ApprovedKnowledgeInput(
        content,
        hashlib.sha256(content.encode()).hexdigest(),
        (),
        ("domain",),
        None,
        None,
        ("fixture",),
        "user",
    )
    record = backend.create_approved(value, "operation-1")
    assert backend.get(record.id) == record
