#!/usr/bin/env python3
# Purpose: Test src/expertiseos/approval/gate.py canonical digest and exact decision binding.

from __future__ import annotations

import dataclasses

import pytest

from expertiseos.approval.gate import ApprovalGate, canonical_approval_digest, child_operation_id
from expertiseos.domain.errors import ApprovalRejectedError, StaleVersionError
from expertiseos.domain.models import (
    CandidateState,
    CreateOperation,
    DecisionGrant,
    PendingOperation,
    PendingOperationKind,
    UserDecisionAction,
)
from tests.consent_support import NOW, approved


def proposal() -> PendingOperation:
    payload = CreateOperation(approved("exact", ("declarative", "conditional_boundary")))
    digest = canonical_approval_digest(PendingOperationKind.CREATE, payload, ())
    return PendingOperation(
        "proposal-1",
        "operation-1",
        "session-1",
        "codex",
        PendingOperationKind.CREATE,
        CandidateState.AWAITING_DECISION,
        payload,
        digest,
        (),
        NOW,
    )


def grant(item: PendingOperation) -> DecisionGrant:
    return DecisionGrant(
        "grant-1",
        item.proposal_id,
        item.session_id,
        item.adapter_id,
        UserDecisionAction.SAVE,
        item.content_digest,
        item.expected_versions,
        "host-user-event-1",
        NOW,
        None,
    )


def test_digest_is_deterministic_and_semantic() -> None:
    item = proposal()
    assert canonical_approval_digest(item.kind, item.payload, ()) == item.content_digest
    assert dataclasses.replace(item, proposal_id="other", operation_id="other").content_digest == (
        item.content_digest
    )
    changed = CreateOperation(approved("changed"))
    assert canonical_approval_digest(item.kind, changed, ()) != item.content_digest


def test_digest_normalizes_unordered_domain_collections() -> None:
    first = CreateOperation(
        approved("exact", ("declarative", "conditional_boundary"), ("domain", "self"))
    )
    reordered = CreateOperation(
        approved("exact", ("conditional_boundary", "declarative"), ("self", "domain"))
    )
    expected = (("knowledge-b", 2), ("knowledge-a", 1))
    reordered_expected = tuple(reversed(expected))
    assert canonical_approval_digest(PendingOperationKind.CREATE, first, expected) == (
        canonical_approval_digest(PendingOperationKind.CREATE, reordered, reordered_expected)
    )


def test_gate_rejects_operation_and_content_changes() -> None:
    item = proposal()
    decision = grant(item)
    gate = ApprovalGate()
    with pytest.raises(ApprovalRejectedError, match="operation_id"):
        gate.validate(item, decision, "different", {}, False)
    changed = dataclasses.replace(item, payload=CreateOperation(approved("changed")))
    with pytest.raises(ApprovalRejectedError, match="changed"):
        gate.validate(changed, decision, item.operation_id, {}, False)


def test_gate_rejects_non_commit_action_and_stale_version() -> None:
    item = dataclasses.replace(proposal(), expected_versions=(("knowledge-1", 1),))
    item = dataclasses.replace(
        item,
        content_digest=canonical_approval_digest(item.kind, item.payload, item.expected_versions),
    )
    decision = grant(item)
    with pytest.raises(StaleVersionError):
        ApprovalGate().validate(item, decision, item.operation_id, {"knowledge-1": 2}, False)
    skipped = dataclasses.replace(decision, action=UserDecisionAction.SKIP)
    with pytest.raises(ApprovalRejectedError, match="action"):
        ApprovalGate().validate(item, skipped, item.operation_id, {"knowledge-1": 1}, False)


def test_grouped_child_operation_ids_are_deterministic_and_distinct() -> None:
    first = child_operation_id("parent", 0, "CreateOperation")
    assert first == child_operation_id("parent", 0, "CreateOperation")
    assert first != child_operation_id("parent", 1, "CreateOperation")
    assert first != child_operation_id("other", 0, "CreateOperation")
