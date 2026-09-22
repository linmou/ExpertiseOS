#!/usr/bin/env python3
# Purpose: Test src/expertiseos/learning/evidence.py validation and pass-only advancement.

from __future__ import annotations

import dataclasses
from datetime import timedelta

import pytest

from expertiseos.domain.errors import DomainValidationError
from expertiseos.domain.models import LearnerState, PendingOperationKind
from expertiseos.learning.evidence import (
    AssistanceLevel,
    EvidenceOutcome,
    LearnerEvidence,
    approved_object_fact,
    validate_evidence,
)
from tests.unit.learning_fakes import NOW, receipt, search_result


def evidence(
    outcome: EvidenceOutcome = EvidenceOutcome.PASS,
    approved_state: LearnerState | None = LearnerState.EXPLAINED,
    contribution: str | None = "I explained the boundary.",
) -> LearnerEvidence:
    return LearnerEvidence(
        "evidence-1",
        "knowledge-1",
        1,
        "task-1",
        "session-1",
        "explain the retry boundary",
        outcome,
        AssistanceLevel.INDEPENDENT,
        "python",
        contribution,
        LearnerState.EXPLAINED,
        approved_state,
        False,
        "evidence-operation-1",
        NOW + timedelta(seconds=1),
    )


def test_actual_c003_search_result_becomes_approved_object_fact() -> None:
    fact = approved_object_fact(search_result(conflicts=("knowledge-2",)), "python")
    assert fact.knowledge_id == "knowledge-1"
    assert fact.knowledge_version == 1
    assert fact.unresolved_relevant_contradiction is True


@pytest.mark.parametrize(
    "outcome",
    [EvidenceOutcome.PARTIAL, EvidenceOutcome.FAIL, EvidenceOutcome.INSUFFICIENT_EVIDENCE],
)
def test_non_pass_outcomes_remain_valid_inspectable_evidence(outcome: EvidenceOutcome) -> None:
    item = evidence(outcome)
    fact = approved_object_fact(search_result(), "python")
    assert validate_evidence(item, fact, receipt()) == item


def test_validation_requires_matching_actual_approval_receipt() -> None:
    item = evidence()
    fact = approved_object_fact(search_result(), "python")
    with pytest.raises(DomainValidationError, match="receipt id"):
        validate_evidence(dataclasses.replace(item, approval_receipt_id="missing"), fact, receipt())
    wrong_kind = dataclasses.replace(receipt(), operation_kind=PendingOperationKind.CONTROL_CHANGE)
    with pytest.raises(DomainValidationError, match="learning evidence"):
        validate_evidence(item, fact, wrong_kind)
    with pytest.raises(DomainValidationError, match="object/version"):
        validate_evidence(item, fact, receipt("knowledge-2"))


def test_validation_rejects_object_version_scope_and_blank_contribution_errors() -> None:
    item = evidence()
    with pytest.raises(DomainValidationError, match="approved object"):
        validate_evidence(item, approved_object_fact(search_result(version=2), "python"), receipt())
    with pytest.raises(DomainValidationError, match="scope"):
        validate_evidence(item, approved_object_fact(search_result(), "rust"), receipt())
    with pytest.raises(DomainValidationError, match="user contribution"):
        dataclasses.replace(item, user_contribution=" ")


def test_applied_or_higher_requires_task_and_known_assistance() -> None:
    item = dataclasses.replace(evidence(), approved_state=LearnerState.APPLIED)
    with pytest.raises(DomainValidationError, match="task reference"):
        dataclasses.replace(item, task_ref=None)
    with pytest.raises(DomainValidationError, match="known assistance"):
        dataclasses.replace(item, assistance_level=AssistanceLevel.UNKNOWN)
