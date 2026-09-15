#!/usr/bin/env python3
# Purpose: Test C002/C003 boundary contracts consumed by C004 pure learning behavior.

from __future__ import annotations

import dataclasses
from dataclasses import MISSING, fields

import pytest

from expertiseos.domain.errors import DomainValidationError
from expertiseos.domain.models import LearnerState
from expertiseos.learning.controls import (
    ApprovedKnowledgeRef,
    ContextScope,
    ControlInspection,
    ControlResolution,
    ControlSettings,
    DeferredActivity,
    FatigueTransition,
    PeriodProgress,
    ReflectionActivityFacts,
    ResponseFacts,
    ScopeExclusion,
)
from expertiseos.learning.evidence import (
    AdvancementThresholds,
    ApprovedObjectFact,
    AssistanceLevel,
    EvidenceOutcome,
    LearnerEvidence,
    LearnerStateSummary,
    LearningInspection,
    approved_object_fact,
    validate_evidence,
)
from tests.unit.learning_fakes import NOW, receipt, search_result


def item() -> LearnerEvidence:
    return LearnerEvidence(
        "evidence-1",
        "knowledge-1",
        1,
        "task-1",
        "session-1",
        "criterion",
        EvidenceOutcome.PASS,
        AssistanceLevel.INDEPENDENT,
        "python",
        "my explanation",
        LearnerState.EXPLAINED,
        LearnerState.EXPLAINED,
        False,
        "evidence-operation-1",
        NOW,
    )


def test_actual_promoted_receipt_and_search_result_satisfy_learning_boundary() -> None:
    evidence = item()
    fact = approved_object_fact(search_result(), "python")
    assert validate_evidence(evidence, fact, receipt()) == evidence


def test_missing_or_stale_producer_fact_fails_before_state_write() -> None:
    writes: list[LearnerEvidence] = []
    fact = approved_object_fact(search_result(version=2), "python")
    with pytest.raises(DomainValidationError):
        writes.append(validate_evidence(item(), fact, receipt()))
    assert writes == []


def test_different_receipt_payload_cannot_reuse_operation_identity() -> None:
    changed = dataclasses.replace(item(), knowledge_id="knowledge-2")
    with pytest.raises(DomainValidationError):
        validate_evidence(
            changed,
            approved_object_fact(search_result("knowledge-2"), "python"),
            receipt(),
        )


def test_all_c004_dataclasses_require_explicit_instantiation_fields() -> None:
    data_types = (
        AdvancementThresholds,
        ApprovedObjectFact,
        LearnerEvidence,
        LearnerStateSummary,
        LearningInspection,
        ControlSettings,
        PeriodProgress,
        ControlResolution,
        FatigueTransition,
        ResponseFacts,
        ReflectionActivityFacts,
        ContextScope,
        ScopeExclusion,
        ApprovedKnowledgeRef,
        DeferredActivity,
        ControlInspection,
    )
    for data_type in data_types:
        assert all(field.default is MISSING for field in fields(data_type))
        assert all(field.default_factory is MISSING for field in fields(data_type))
