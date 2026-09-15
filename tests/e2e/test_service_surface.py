#!/usr/bin/env python3
# Purpose: Test src/expertiseos/service.py typed reads and guarded commit outcomes.

from __future__ import annotations

import dataclasses
from datetime import timedelta

import pytest

from expertiseos.domain.models import CandidateState, CommitStatus, LearnerState
from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionBinding,
    DecisionObservation,
    DecisionRejection,
    EventKind,
    HostEvent,
)
from expertiseos.knowledge.backend import SearchQuery
from expertiseos.learning.evidence import (
    AssistanceLevel,
    EvidenceOutcome,
    LearnerEvidence,
)
from expertiseos.ownership import DeletionScope, KnowledgeRef
from expertiseos.service import ExpertiseOSService, ToolStatus
from tests.backend_support import approved
from tests.consent_support import NOW
from tests.e2e.conftest import ProductGraph
from tests.fakes import FakeHostAdapter


def _facade(graph: ProductGraph) -> ExpertiseOSService:
    return ExpertiseOSService(graph.knowledge, graph.backend, graph.state, ())


def _grant(graph: ProductGraph, proposal_id: str, grant_id: str) -> None:
    graph.knowledge.register_decision(
        proposal_id,
        grant_id,
        DecisionObservation(
            True,
            DecisionAction.SAVE,
            f"user-event:{proposal_id}",
            DecisionRejection.NONE,
        ),
        NOW + timedelta(seconds=1),
    )


def test_reads_distinguish_ok_rejected_and_degraded(product_graph: ProductGraph) -> None:
    facade = _facade(product_graph)

    missing = facade.get_knowledge("missing", None, False)
    healthy = facade.health()
    search = facade.search_knowledge(SearchQuery("anything", 5, None, (), (), ()))

    assert missing.status is ToolStatus.REJECTED
    assert missing.error_code == "not_found"
    assert healthy.status is ToolStatus.OK
    assert search.status is ToolStatus.OK

    product_graph.cli.fail_search = True
    degraded = facade.search_knowledge(SearchQuery("anything", 5, None, (), (), ()))
    assert degraded.status is ToolStatus.DEGRADED


def test_only_committed_result_renders_saved(product_graph: ProductGraph) -> None:
    facade = _facade(product_graph)
    proposal = product_graph.knowledge.propose_create(
        "proposal-surface",
        "operation-surface",
        "session-surface",
        "host-test",
        approved("surface approved value", None, ("fact",), ("domain",), ("event-1",)),
        NOW,
    )
    product_graph.knowledge.present(proposal.proposal_id)

    rejected = facade.commit_proposal(
        proposal.proposal_id, "missing-grant", proposal.operation_id, {}
    )
    assert rejected.status is ToolStatus.REJECTED
    assert rejected.message != "Saved"

    host = FakeHostAdapter("host-test", "session-surface", ())
    host.on_session_start(
        HostEvent(
            "start-surface",
            "host-test",
            "session-surface",
            EventKind.SESSION_START,
            NOW,
            None,
            None,
        )
    )
    event = HostEvent(
        "save-surface",
        "host-test",
        "session-surface",
        EventKind.USER_INPUT,
        NOW + timedelta(seconds=1),
        "user-event-surface",
        DecisionAction.SAVE,
    )
    host.on_user_event(event)
    decision = host.register_decision_if_unambiguous(
        event,
        DecisionBinding(
            proposal.proposal_id,
            proposal.kind.value,
            proposal.adapter_id,
            proposal.session_id,
            proposal.content_digest,
            proposal.expected_versions,
            (DecisionAction.SAVE,),
        ),
    )
    product_graph.knowledge.register_decision(
        proposal.proposal_id,
        "grant-surface",
        decision,
        NOW + timedelta(seconds=2),
    )

    committed = facade.commit_proposal(
        proposal.proposal_id, "grant-surface", proposal.operation_id, {}
    )
    replay = facade.commit_proposal(
        proposal.proposal_id, "grant-surface", proposal.operation_id, {}
    )

    assert committed.status is ToolStatus.COMMITTED
    assert committed.message == "Saved"
    assert replay.status is ToolStatus.COMMITTED
    assert replay.data == committed.data
    assert (
        product_graph.knowledge.commit(
            proposal.proposal_id, "grant-surface", proposal.operation_id
        ).status
        is CommitStatus.COMMITTED
    )


def test_learning_receipt_before_writer_failure_is_incomplete_then_retries_once(
    product_graph: ProductGraph, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade = _facade(product_graph)
    knowledge = product_graph.backend.create_approved(
        approved("learn this", None, ("fact",), ("domain",), ("event-learning",)),
        "seed-learning",
    )
    operation_id = "learning-operation"
    evidence = LearnerEvidence(
        "evidence-1",
        knowledge.id,
        knowledge.version,
        "task-1",
        "session-learning",
        "apply the retry rule",
        EvidenceOutcome.PASS,
        AssistanceLevel.INDEPENDENT,
        "python",
        "user applied it",
        LearnerState.RECOGNIZED,
        LearnerState.RECOGNIZED,
        False,
        operation_id,
        NOW,
    )
    proposal = facade.propose_learning_evidence(
        "learning-proposal",
        operation_id,
        "session-learning",
        "codex",
        evidence,
        {knowledge.id: knowledge.version},
        NOW,
    )
    assert proposal.status is ToolStatus.OK
    _grant(product_graph, "learning-proposal", "learning-grant")
    original_insert = product_graph.state.insert_evidence_once
    failed = False

    def fail_once(value: LearnerEvidence) -> LearnerEvidence:
        nonlocal failed
        if not failed:
            failed = True
            raise OSError("writer unavailable")
        return original_insert(value)

    monkeypatch.setattr(product_graph.state, "insert_evidence_once", fail_once)

    incomplete = facade.commit_proposal(
        "learning-proposal",
        "learning-grant",
        operation_id,
        {knowledge.id: 999},
    )
    committed = facade.commit_proposal(
        "learning-proposal",
        "learning-grant",
        operation_id,
        {knowledge.id: knowledge.version},
    )
    replay = facade.commit_proposal(
        "learning-proposal",
        "learning-grant",
        operation_id,
        {knowledge.id: knowledge.version},
    )

    assert incomplete.status is ToolStatus.INCOMPLETE
    assert incomplete.render_saved is False
    assert product_graph.state.get_receipt(operation_id) is not None
    assert committed.status is replay.status is ToolStatus.COMMITTED
    assert committed.render_saved is replay.render_saved is True
    assert product_graph.state.list_evidence(knowledge.id, 1, "python", 20) == (evidence,)
    grant = product_graph.grants.get("learning-grant")
    candidate = product_graph.candidates.get("learning-proposal")
    assert grant is not None and grant.consumed_at is not None
    assert candidate is not None and candidate.state is CandidateState.APPROVED

    divergent_evidence = dataclasses.replace(
        evidence,
        id="evidence-divergent",
        criterion="different criterion",
    )
    divergent_proposal = facade.propose_learning_evidence(
        "learning-divergent",
        operation_id,
        "session-learning",
        "codex",
        divergent_evidence,
        {knowledge.id: knowledge.version},
        NOW,
    )
    assert divergent_proposal.status is ToolStatus.OK
    _grant(product_graph, "learning-divergent", "learning-divergent-grant")
    divergent = facade.commit_proposal(
        "learning-divergent",
        "learning-divergent-grant",
        operation_id,
        {knowledge.id: knowledge.version},
    )
    assert divergent.status is ToolStatus.CONFLICT
    assert product_graph.state.list_evidence(knowledge.id, 1, "python", 20) == (evidence,)


def test_delegated_stale_and_divergent_attempts_do_not_bypass_binding(
    product_graph: ProductGraph,
) -> None:
    facade = _facade(product_graph)
    knowledge = product_graph.backend.create_approved(
        approved("version one", None, ("fact",), ("domain",), ("event-1",)),
        "seed-v1",
    )
    evidence = LearnerEvidence(
        "evidence-stale",
        knowledge.id,
        1,
        "task-stale",
        "session-stale",
        "criterion",
        EvidenceOutcome.PASS,
        AssistanceLevel.INDEPENDENT,
        None,
        "user contribution",
        LearnerState.RECOGNIZED,
        LearnerState.RECOGNIZED,
        False,
        "stale-operation",
        NOW,
    )
    facade.propose_learning_evidence(
        "stale-proposal",
        "stale-operation",
        "session-stale",
        "codex",
        evidence,
        {knowledge.id: 1},
        NOW,
    )
    _grant(product_graph, "stale-proposal", "stale-grant")
    product_graph.backend.update_approved(
        knowledge.id,
        1,
        approved("version two", None, ("fact",), ("domain",), ("event-2",)),
        "seed-v2",
    )

    stale = facade.commit_proposal(
        "stale-proposal", "stale-grant", "stale-operation", {knowledge.id: 1}
    )

    assert stale.status is ToolStatus.CONFLICT
    assert product_graph.state.get_receipt("stale-operation") is None


def test_delete_dispatch_uses_actual_c007_writer_and_readback(
    product_graph: ProductGraph,
) -> None:
    facade = _facade(product_graph)
    record = product_graph.backend.create_approved(
        approved("delete exact", None, ("fact",), ("domain",), ("event-delete",)),
        "seed-delete",
    )
    scope = DeletionScope(
        (KnowledgeRef(record.id, record.version),),
        True,
        True,
        True,
        ("host backups remain external",),
    )
    proposed = facade.propose_retire_or_delete(
        "delete-proposal",
        "delete-operation",
        "session-delete",
        "codex",
        scope,
        {record.id: record.version},
        NOW,
    )
    assert proposed.status is ToolStatus.OK
    _grant(product_graph, "delete-proposal", "delete-grant")
    deleted = facade.commit_proposal(
        "delete-proposal",
        "delete-grant",
        "delete-operation",
        {record.id: 999},
    )

    assert deleted.status is ToolStatus.COMMITTED
    assert product_graph.backend.get(record.id, record.version, True) is None
    assert product_graph.state.get_receipt("delete-operation") is not None
