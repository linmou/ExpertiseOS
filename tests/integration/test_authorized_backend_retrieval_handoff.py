#!/usr/bin/env python3
# Purpose: Test C002-authorized commits through C003 canonical retrieval and fallback.

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from expertiseos.approval.gate import ApprovalGate, DecisionGrantStore
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.domain.models import CommitStatus
from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionBinding,
    EventKind,
    HostEvent,
)
from expertiseos.knowledge.backend import SearchMode, SearchQuery, TrustLevel
from expertiseos.knowledge.service import KnowledgeService
from expertiseos.state.sqlite import SQLiteState
from tests.backend_support import FakeBasicMemoryCli, approved, backend
from tests.consent_support import NOW
from tests.fakes import DeterministicClock, FakeHostAdapter

pytestmark = pytest.mark.integration


def _authorize(
    service: KnowledgeService,
    host: FakeHostAdapter,
    proposal_id: str,
    operation_id: str,
    content: str,
    user_event_ref: str,
    offset_seconds: int,
) -> tuple[str, str]:
    proposal = service.propose_create(
        proposal_id,
        operation_id,
        host.session_id,
        host.adapter_id,
        approved(
            content,
            "python",
            ("procedure",),
            ("domain",),
            (user_event_ref,),
        ),
        NOW + timedelta(seconds=offset_seconds),
    )
    service.present(proposal_id)
    event = HostEvent(
        f"event-{proposal_id}",
        host.adapter_id,
        host.session_id,
        EventKind.USER_INPUT,
        NOW + timedelta(seconds=offset_seconds + 1),
        user_event_ref,
        DecisionAction.SAVE,
    )
    host.on_user_event(event)
    observation = host.register_decision_if_unambiguous(
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
    grant = service.register_decision(
        proposal_id,
        f"grant-{proposal_id}",
        observation,
        NOW + timedelta(seconds=offset_seconds + 2),
    )
    return proposal.operation_id, grant.grant_id


def test_authorized_commit_is_the_record_consumed_by_recall_and_fallback(
    tmp_path: Path,
) -> None:
    cli = FakeBasicMemoryCli()
    store = backend(tmp_path, cli)
    receipts = SQLiteState(":memory:")
    service = KnowledgeService(
        store,
        CandidateStore(),
        DecisionGrantStore(),
        ApprovalGate(),
        receipts,
        DeterministicClock(NOW + timedelta(hours=1), timedelta(seconds=1)),
    )
    host = FakeHostAdapter("codex", "session-e02", ())
    host.on_session_start(
        HostEvent("start-e02", "codex", "session-e02", EventKind.SESSION_START, NOW, None, None)
    )
    query = SearchQuery(
        "authorized retry boundary",
        5,
        "python",
        ("domain",),
        ("procedure",),
        (),
    )

    operation_id, grant_id = _authorize(
        service,
        host,
        "proposal-e02",
        "operation-e02",
        "authorized retry boundary",
        "host-user-e02",
        1,
    )
    assert service.search(query).results == ()

    committed = service.commit("proposal-e02", grant_id, operation_id)

    assert committed.status is CommitStatus.COMMITTED
    assert committed.receipt is not None
    assert committed.receipt.user_event_ref == "host-user-e02"
    record = committed.records[0]
    assert service.get(record.id, record.version, True) == record
    recalled = service.search(query)
    assert recalled.mode is SearchMode.LOCAL_INDEXED
    assert recalled.results[0].knowledge_id == record.id
    assert recalled.results[0].version == record.version
    assert recalled.results[0].source_refs == record.source_refs
    assert recalled.results[0].trust is TrustLevel.UNTRUSTED_DATA

    notes_after_commit = dict(cli.notes)
    assert service.commit("proposal-e02", grant_id, operation_id) == committed
    assert cli.notes == notes_after_commit

    cli.fail_search = True
    fallback = service.search(query)
    assert fallback.mode is SearchMode.KEYWORD
    assert fallback.degraded is True
    assert fallback.results[0].knowledge_id == record.id
    assert fallback.results[0].version == record.version
    assert cli.notes == notes_after_commit
    receipts.close()


def test_divergent_operation_replay_cannot_mutate_canonical_storage(tmp_path: Path) -> None:
    cli = FakeBasicMemoryCli()
    store = backend(tmp_path, cli)
    receipts = SQLiteState(":memory:")
    service = KnowledgeService(
        store,
        CandidateStore(),
        DecisionGrantStore(),
        ApprovalGate(),
        receipts,
        DeterministicClock(NOW + timedelta(hours=1), timedelta(seconds=1)),
    )
    host = FakeHostAdapter("codex", "session-e02-replay", ())
    host.on_session_start(
        HostEvent(
            "start-e02-replay",
            "codex",
            "session-e02-replay",
            EventKind.SESSION_START,
            NOW,
            None,
            None,
        )
    )
    operation_id, first_grant = _authorize(
        service,
        host,
        "proposal-e02-first",
        "operation-e02-reused",
        "original authorized content",
        "host-user-e02-first",
        1,
    )
    first = service.commit("proposal-e02-first", first_grant, operation_id)
    assert first.status is CommitStatus.COMMITTED
    notes_after_first = dict(cli.notes)

    _, divergent_grant = _authorize(
        service,
        host,
        "proposal-e02-divergent",
        operation_id,
        "divergent authorized content",
        "host-user-e02-divergent",
        10,
    )
    divergent = service.commit("proposal-e02-divergent", divergent_grant, operation_id)

    assert divergent.status is CommitStatus.REJECTED
    assert divergent.records == ()
    assert cli.notes == notes_after_first
    assert (
        service.search(SearchQuery("divergent authorized content", 5, None, (), (), ())).results
        == ()
    )
    receipts.close()
