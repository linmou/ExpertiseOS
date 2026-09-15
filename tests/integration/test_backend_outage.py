#!/usr/bin/env python3
# Purpose: Test honest commit and UI outcomes during canonical backend outages.

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from expertiseos.domain.models import CommitResult, CommitStatus
from expertiseos.knowledge.backend import IndexState, SearchMode, StoreState
from expertiseos.reliability import classify_commit
from tests.fakes import DeterministicClock, DeterministicIdGenerator, FakeKnowledgeBackend


def test_backend_failure_never_renders_saved() -> None:
    backend = FakeKnowledgeBackend(
        DeterministicClock(datetime(2026, 9, 14, tzinfo=UTC), timedelta(seconds=1)),
        DeterministicIdGenerator("knowledge", 1),
        StoreState.UNAVAILABLE,
        IndexState.UNAVAILABLE,
        SearchMode.UNAVAILABLE,
    )
    outcome = classify_commit(
        CommitResult(CommitStatus.FAILED, (), None, "canonical_unavailable"), backend
    )
    assert not outcome.render_saved
    assert outcome.error_code == "canonical_unavailable"
