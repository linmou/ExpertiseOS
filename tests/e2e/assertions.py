#!/usr/bin/env python3
# Purpose: Assert C008 persistent deltas and volatile-state expiry through public contracts.

from __future__ import annotations

from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.knowledge.backend import SearchQuery
from expertiseos.knowledge.service import KnowledgeService
from expertiseos.state.sqlite import SQLiteState


def assert_marker_absent(
    service: KnowledgeService,
    state: SQLiteState,
    candidates: CandidateStore,
    marker: str,
    proposal_id: str,
    operation_id: str,
) -> None:
    """Prove a candidate marker crossed neither approved reads nor durable receipts."""
    assert service.search(SearchQuery(marker, 20, None, (), (), ())).results == ()
    assert state.get_receipt(operation_id) is None
    assert candidates.get(proposal_id) is None


def assert_exact_record_delta(
    service: KnowledgeService,
    knowledge_id: str,
    version: int,
    expected_content: str,
) -> None:
    """Prove the approved record and version are immediately readable exactly."""
    record = service.get(knowledge_id, version, True)
    assert record is not None
    assert record.content == expected_content
    assert record.version == version
