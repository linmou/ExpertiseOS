#!/usr/bin/env python3
# Purpose: Test bounded inspection in src/expertiseos/learning/evidence.py and controls.py.

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from expertiseos.domain.errors import DomainValidationError
from expertiseos.domain.models import LearnerState
from expertiseos.learning.controls import (
    ApprovedKnowledgeRef,
    ContextScope,
    DeferredActivity,
    DeferredStatus,
    ExclusionKind,
    PeriodProgress,
    ScopeExclusion,
    default_daily_settings,
    inspect_controls,
)
from expertiseos.learning.evidence import (
    AssistanceLevel,
    EvidenceOutcome,
    LearnerEvidence,
    LearnerStateSummary,
    inspect_learning_state,
)
from tests.unit.learning_fakes import NOW


def evidence(identifier: str) -> LearnerEvidence:
    return LearnerEvidence(
        identifier,
        "knowledge-1",
        1,
        "task-1",
        "session-1",
        "criterion",
        EvidenceOutcome.PASS,
        AssistanceLevel.ASSISTED,
        "python",
        "my contribution",
        LearnerState.EXPLAINED,
        LearnerState.EXPLAINED,
        False,
        f"operation-{identifier}",
        NOW,
    )


def test_learning_inspection_is_bounded_and_side_effect_free() -> None:
    summary = LearnerStateSummary(
        "knowledge-1", 1, "python", LearnerState.EXPLAINED, ("e1", "e2"), (), (), NOW
    )
    records = (evidence("e1"), evidence("e2"))
    result = inspect_learning_state(summary, records, 1)
    assert tuple(item.id for item in result.supporting_evidence) == ("e1",)
    assert result.truncated is True
    with pytest.raises(DomainValidationError, match="limit"):
        inspect_learning_state(summary, records, 0)


def test_control_inspection_bounds_exclusions_and_deferred_activities() -> None:
    settings = default_daily_settings("UTC", 1)
    progress = PeriodProgress("2026-09-14", 0, Decimal("0"), (), ())
    exclusions = tuple(
        ScopeExclusion(f"x-{index}", ExclusionKind.SOURCE, f"source-{index}", NOW, "op")
        for index in range(2)
    )
    deferred = tuple(
        DeferredActivity(
            f"d-{index}",
            (ApprovedKnowledgeRef("knowledge-1", 1),),
            "explain",
            NOW + timedelta(seconds=index),
            DeferredStatus.PENDING,
            "op",
        )
        for index in range(2)
    )
    result = inspect_controls(settings, progress, exclusions, deferred, NOW, 1)
    assert len(result.exclusions) == 1
    assert len(result.deferred_activities) == 1
    assert result.truncated is True
    assert ContextScope(None, None, None).path is None
