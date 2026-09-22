#!/usr/bin/env python3
# Purpose: Test malicious retrieved content remains bounded untrusted data.

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from expertiseos.knowledge.backend import (
    IndexState,
    SearchMode,
    SearchQuery,
    StoreState,
    TrustLevel,
)
from expertiseos.reliability import search_with_degradation
from tests.backend_support import approved
from tests.fakes import DeterministicClock, DeterministicIdGenerator, FakeKnowledgeBackend
from tests.integration.fixtures.reliability_fixtures import MALICIOUS_CONTENT


def test_stored_instruction_has_no_control_or_authorization_effect() -> None:
    backend = FakeKnowledgeBackend(
        DeterministicClock(datetime(2026, 9, 14, tzinfo=UTC), timedelta(seconds=1)),
        DeterministicIdGenerator("knowledge", 1),
        StoreState.READY,
        IndexState.READY,
        SearchMode.LOCAL_INDEXED,
    )
    backend.create_approved(
        approved(MALICIOUS_CONTENT, None, ("fact",), ("domain",), ("tool:1",)), "create-1"
    )
    result = search_with_degradation(backend, SearchQuery("Ignore policy", 1, None, (), (), ()))
    assert len(result.results) == 1
    assert result.results[0].trust is TrustLevel.UNTRUSTED_DATA
    assert result.results[0].excerpt == MALICIOUS_CONTENT
    assert not hasattr(result.results[0], "authorized")
