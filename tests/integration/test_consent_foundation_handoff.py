#!/usr/bin/env python3
# Purpose: Test C001 host/backend outputs through C002 consent, receipt, and read-back.

from __future__ import annotations

from datetime import timedelta

import pytest

from expertiseos.domain.models import CommitStatus
from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionBinding,
    EventKind,
    HostEvent,
)
from tests.consent_support import NOW, approved, service_bundle
from tests.fakes import FakeHostAdapter

pytestmark = pytest.mark.integration


def test_actual_c001_host_and_backend_outputs_cross_c002_consent_boundary() -> None:
    bundle = service_bundle()
    proposal = bundle.service.propose_create(
        "proposal-e01",
        "operation-e01",
        "session-e01",
        "codex",
        approved("approved E01 knowledge", source_refs=("host-user-e01",)),
        NOW,
    )
    bundle.service.present(proposal.proposal_id)

    host = FakeHostAdapter("codex", "session-e01", ())
    host.on_session_start(
        HostEvent(
            "start-e01",
            "codex",
            "session-e01",
            EventKind.SESSION_START,
            NOW,
            None,
            None,
        )
    )
    user_event = HostEvent(
        "event-e01",
        "codex",
        "session-e01",
        EventKind.USER_INPUT,
        NOW + timedelta(seconds=1),
        "host-user-e01",
        DecisionAction.SAVE,
    )
    host.on_user_event(user_event)
    observation = host.register_decision_if_unambiguous(
        user_event,
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

    grant = bundle.service.register_decision(
        proposal.proposal_id,
        "grant-e01",
        observation,
        NOW + timedelta(seconds=2),
    )
    result = bundle.service.commit(
        proposal.proposal_id,
        grant.grant_id,
        proposal.operation_id,
    )

    assert result.status is CommitStatus.COMMITTED
    assert result.receipt is not None
    assert result.receipt.user_event_ref == "host-user-e01"
    assert result.records[0] == bundle.backend.get("knowledge-1", 1)
    assert bundle.receipts.get_receipt("operation-e01") == result.receipt
