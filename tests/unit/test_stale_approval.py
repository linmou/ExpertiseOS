#!/usr/bin/env python3
# Purpose: Test gate.py and service.py rejection of forged, replayed, and changed approval.

from __future__ import annotations

import dataclasses

import pytest

from expertiseos.domain.errors import ApprovalRejectedError
from expertiseos.domain.models import CommitStatus, CreateOperation
from expertiseos.hosts.contract import DecisionAction, DecisionObservation, DecisionRejection
from tests.consent_support import NOW, approved, present_create, service_bundle


def test_model_boolean_or_text_cannot_commit_without_grant() -> None:
    bundle = service_bundle()
    bundle.service.propose_create("p", "o", "s", "codex", approved("candidate"), NOW)
    bundle.service.present("p")
    result = bundle.service.commit("p", "approved=true", "o")
    assert result.status is CommitStatus.REJECTED
    assert bundle.backend.get_current_versions(()) == {}
    assert bundle.receipts.get_receipt("o") is None


@pytest.mark.parametrize(
    "rejection",
    [
        DecisionRejection.NOT_USER_INPUT,
        DecisionRejection.MISSING_USER_PROVENANCE,
        DecisionRejection.AMBIGUOUS_ACTION,
        DecisionRejection.ALREADY_OBSERVED,
    ],
)
def test_unmatched_model_tool_or_quoted_observation_cannot_create_grant(
    rejection: DecisionRejection,
) -> None:
    bundle = service_bundle()
    bundle.service.propose_create("p", "o", "s", "codex", approved("candidate"), NOW)
    bundle.service.present("p")
    forged = DecisionObservation(False, None, None, rejection)
    with pytest.raises(ApprovalRejectedError):
        bundle.service.register_decision("p", "g", forged, NOW)


def test_content_change_after_grant_rejects_old_decision() -> None:
    bundle = service_bundle()
    proposal_id, grant_id = present_create(bundle, "before")
    current = bundle.candidates.get(proposal_id)
    assert current is not None
    changed = dataclasses.replace(current, payload=CreateOperation(approved("after")))
    bundle.candidates.replace_awaiting_decision(changed)
    assert bundle.service.commit(proposal_id, grant_id, "operation-1").status is (
        CommitStatus.REJECTED
    )


def test_skip_action_does_not_authorize_commit() -> None:
    bundle = service_bundle()
    bundle.service.propose_create("p", "o", "s", "codex", approved("candidate"), NOW)
    bundle.service.present("p")
    skip = DecisionObservation(True, DecisionAction.SKIP, "event-skip", DecisionRejection.NONE)
    bundle.service.register_decision("p", "g", skip, NOW)
    assert bundle.service.commit("p", "g", "o").status is CommitStatus.REJECTED
