#!/usr/bin/env python3
# Purpose: Test src/expertiseos/learning/controls.py minimal deferred activity behavior.

from __future__ import annotations

import dataclasses
from datetime import timedelta

import pytest

from expertiseos.domain.errors import DomainValidationError
from expertiseos.learning.controls import (
    ApprovedKnowledgeRef,
    ControlReason,
    ControlResolution,
    DeferredActivity,
    DeferredStatus,
    can_offer_deferred,
    remove_deferred,
    validate_deferred_activity,
)
from expertiseos.learning.evidence import ApprovedObjectFact
from tests.unit.learning_fakes import NOW


def activity() -> DeferredActivity:
    return DeferredActivity(
        "deferred-1",
        (ApprovedKnowledgeRef("knowledge-1", 1),),
        "explain_boundary",
        NOW,
        DeferredStatus.PENDING,
        "control-operation-1",
    )


def resolution(reason: ControlReason) -> ControlResolution:
    active = reason is ControlReason.ACTIVE
    recall = reason is not ControlReason.DISABLED
    return ControlResolution(reason, active, active, active, recall, None)


def test_valid_activity_contains_only_approved_versioned_references() -> None:
    item = activity()
    facts = (ApprovedObjectFact("knowledge-1", 1, "python", False),)
    assert validate_deferred_activity(item, facts) == item
    assert not hasattr(item, "content")


def test_missing_stale_or_duplicate_references_are_rejected() -> None:
    facts = (ApprovedObjectFact("knowledge-1", 2, "python", False),)
    with pytest.raises(DomainValidationError, match="approved knowledge"):
        validate_deferred_activity(activity(), facts)
    duplicate = dataclasses.replace(
        activity(), knowledge_refs=(ApprovedKnowledgeRef("knowledge-1", 1),) * 2
    )
    with pytest.raises(DomainValidationError, match="duplicate"):
        validate_deferred_activity(
            duplicate, (ApprovedObjectFact("knowledge-1", 1, "python", False),)
        )


@pytest.mark.parametrize("reason", list(ControlReason))
def test_offer_requires_later_active_foreground_session(reason: ControlReason) -> None:
    item = activity()
    active = reason is ControlReason.ACTIVE
    assert can_offer_deferred(item, resolution(reason), True, NOW + timedelta(seconds=1)) is active
    assert can_offer_deferred(item, resolution(reason), False, NOW + timedelta(seconds=1)) is False
    assert can_offer_deferred(item, resolution(reason), True, NOW - timedelta(seconds=1)) is False


def test_removed_activity_is_not_offered() -> None:
    removed = remove_deferred(activity(), "remove-operation-1")
    assert removed.status is DeferredStatus.REMOVED
    assert removed.approval_receipt_id == "remove-operation-1"
    offered = can_offer_deferred(
        removed, resolution(ControlReason.ACTIVE), True, NOW + timedelta(1)
    )
    assert offered is False
