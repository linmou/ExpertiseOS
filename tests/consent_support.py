#!/usr/bin/env python3
# Purpose: Provide C002-owned deterministic helpers for consent-core tests.

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from expertiseos.approval.gate import ApprovalGate, DecisionGrantStore
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionObservation,
    DecisionRejection,
)
from expertiseos.knowledge.backend import (
    ApprovedKnowledgeInput,
    IndexState,
    SearchMode,
    StoreState,
)
from expertiseos.knowledge.service import KnowledgeService
from expertiseos.state.sqlite import SQLiteState
from tests.fakes import DeterministicClock, DeterministicIdGenerator, FakeKnowledgeBackend

NOW = datetime(2026, 9, 14, tzinfo=UTC)


def approved(
    content: str,
    categories: tuple[str, ...] = (),
    subjects: tuple[str, ...] = ("domain",),
    source_refs: tuple[str, ...] = ("host-event-1",),
    contribution_origin: str = "user",
) -> ApprovedKnowledgeInput:
    return ApprovedKnowledgeInput(
        content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
        categories,
        subjects,
        None,
        None,
        source_refs,
        contribution_origin,
    )


def observation(
    action: DecisionAction = DecisionAction.SAVE,
    user_event_ref: str = "host-user-event-1",
) -> DecisionObservation:
    return DecisionObservation(True, action, user_event_ref, DecisionRejection.NONE)


def fake_backend() -> FakeKnowledgeBackend:
    return FakeKnowledgeBackend(
        DeterministicClock(NOW, timedelta(seconds=1)),
        DeterministicIdGenerator("knowledge", 1),
        StoreState.READY,
        IndexState.READY,
        SearchMode.KEYWORD,
    )


@dataclass(frozen=True)
class ServiceBundle:
    service: KnowledgeService
    backend: FakeKnowledgeBackend
    candidates: CandidateStore
    grants: DecisionGrantStore
    receipts: SQLiteState


def service_bundle(backend: FakeKnowledgeBackend | None = None) -> ServiceBundle:
    selected = fake_backend() if backend is None else backend
    candidates = CandidateStore()
    grants = DecisionGrantStore()
    receipts = SQLiteState(":memory:")
    service = KnowledgeService(
        selected,
        candidates,
        grants,
        ApprovalGate(),
        receipts,
        DeterministicClock(NOW + timedelta(hours=1), timedelta(seconds=1)),
    )
    return ServiceBundle(service, selected, candidates, grants, receipts)


def present_create(
    bundle: ServiceBundle,
    content: str = "approved content",
    proposal_id: str = "proposal-1",
    operation_id: str = "operation-1",
    session_id: str = "session-1",
    adapter_id: str = "codex",
) -> tuple[str, str]:
    bundle.service.propose_create(
        proposal_id,
        operation_id,
        session_id,
        adapter_id,
        approved(content),
        NOW,
    )
    bundle.service.present(proposal_id)
    bundle.service.register_decision(
        proposal_id,
        f"grant-{proposal_id}",
        observation(user_event_ref=f"host-user-event-{proposal_id}"),
        NOW + timedelta(minutes=1),
    )
    return proposal_id, f"grant-{proposal_id}"
