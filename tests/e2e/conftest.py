#!/usr/bin/env python3
# Purpose: Build the promoted C002-C004 service graph over the real C003 backend adapter.

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pytest

from expertiseos.approval.gate import ApprovalGate, DecisionGrantStore
from expertiseos.backends.basic_memory import BasicMemoryBackend
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.knowledge.service import KnowledgeService
from expertiseos.state.sqlite import SQLiteState
from tests.backend_support import FakeBasicMemoryCli, backend
from tests.consent_support import NOW
from tests.fakes import DeterministicClock


@dataclass(frozen=True)
class ProductGraph:
    knowledge: KnowledgeService
    backend: BasicMemoryBackend
    state: SQLiteState
    candidates: CandidateStore
    grants: DecisionGrantStore
    cli: FakeBasicMemoryCli


@pytest.fixture
def product_graph(tmp_path: Path) -> Generator[ProductGraph, None, None]:
    """Create actual promoted component objects; only the external CLI process is faked."""
    cli = FakeBasicMemoryCli()
    knowledge_backend = backend(tmp_path / "basic-memory", cli)
    candidates = CandidateStore()
    grants = DecisionGrantStore()
    state = SQLiteState(tmp_path / "state.sqlite")
    knowledge = KnowledgeService(
        knowledge_backend,
        candidates,
        grants,
        ApprovalGate(),
        state,
        DeterministicClock(NOW + timedelta(hours=1), timedelta(seconds=1)),
    )
    graph = ProductGraph(knowledge, knowledge_backend, state, candidates, grants, cli)
    yield graph
    state.close()
