#!/usr/bin/env python3
# Purpose: Test src/expertiseos/service.py typed reads and guarded commit outcomes.

from __future__ import annotations

from datetime import timedelta

from expertiseos.domain.models import CommitStatus
from expertiseos.hosts.contract import DecisionAction, DecisionBinding, EventKind, HostEvent
from expertiseos.knowledge.backend import SearchQuery
from expertiseos.service import ExpertiseOSService, ToolStatus
from tests.backend_support import approved
from tests.consent_support import NOW
from tests.e2e.conftest import ProductGraph
from tests.fakes import FakeHostAdapter


def _facade(graph: ProductGraph) -> ExpertiseOSService:
    return ExpertiseOSService(graph.knowledge, graph.backend, graph.state, ())


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

    rejected = facade.commit_proposal(proposal.proposal_id, "missing-grant", proposal.operation_id)
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

    committed = facade.commit_proposal(proposal.proposal_id, "grant-surface", proposal.operation_id)
    replay = facade.commit_proposal(proposal.proposal_id, "grant-surface", proposal.operation_id)

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


def test_missing_guarded_upstream_mutation_producers_are_unavailable(
    product_graph: ProductGraph,
) -> None:
    facade = _facade(product_graph)

    assert facade.propose_learning_evidence("learning-1", object()).status is ToolStatus.UNAVAILABLE
    assert facade.propose_control_change("control-1", object()).status is ToolStatus.UNAVAILABLE
    assert facade.propose_retire_or_delete("delete-1", object()).status is ToolStatus.UNAVAILABLE
