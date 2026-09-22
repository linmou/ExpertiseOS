#!/usr/bin/env python3
# Purpose: Build the real promoted service graph for C008 integration handoff tests.

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from expertiseos.approval.gate import ApprovalGate, DecisionGrantStore
from expertiseos.backends.basic_memory import BasicMemoryBackend
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.knowledge.service import KnowledgeService
from expertiseos.state.sqlite import SQLiteState
from tests.backend_support import FakeBasicMemoryCli, backend
from tests.consent_support import NOW
from tests.fakes import DeterministicClock


@dataclass(frozen=True)
class ProductHandoffGraph:
    knowledge: KnowledgeService
    backend: BasicMemoryBackend
    state: SQLiteState
    candidates: CandidateStore
    grants: DecisionGrantStore
    cli: FakeBasicMemoryCli


def build_product_handoff_graph(tmp_path: Path) -> ProductHandoffGraph:
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
    return ProductHandoffGraph(knowledge, knowledge_backend, state, candidates, grants, cli)
