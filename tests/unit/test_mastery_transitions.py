#!/usr/bin/env python3
# Purpose: Test src/expertiseos/learning/evidence.py deterministic mastery transitions.

from __future__ import annotations

import dataclasses
from datetime import timedelta

import pytest

from expertiseos.domain.errors import DomainValidationError
from expertiseos.domain.models import LearnerState
from expertiseos.learning.evidence import (
    AdvancementThresholds,
    ApprovedObjectFact,
    AssistanceLevel,
    EvidenceOutcome,
    LearnerEvidence,
    LearnerStateSummary,
    summarize_mastery,
)
from tests.unit.learning_fakes import NOW


def thresholds() -> AdvancementThresholds:
    return AdvancementThresholds(1, 1, 1, 1, 2)


def evidence(
    identifier: str,
    state: LearnerState,
    *,
    outcome: EvidenceOutcome = EvidenceOutcome.PASS,
    version: int = 1,
    scope: str | None = "python",
    task: str | None = "task-1",
    session: str = "session-1",
    assistance: AssistanceLevel = AssistanceLevel.ASSISTED,
    transfer: bool = False,
) -> LearnerEvidence:
    return LearnerEvidence(
        identifier,
        "knowledge-1",
        version,
        task,
        session,
        "criterion",
        outcome,
        assistance,
        scope,
        "my contribution",
        state,
        state,
        transfer,
        f"operation-{identifier}",
        NOW + timedelta(seconds=int(identifier.removeprefix("e"))),
    )


def summarize(
    items: tuple[LearnerEvidence, ...], config: AdvancementThresholds | None = None
) -> LearnerStateSummary:
    return summarize_mastery(
        ApprovedObjectFact("knowledge-1", 1, "python", False),
        items,
        thresholds() if config is None else config,
        False,
        NOW + timedelta(hours=1),
    )


def test_no_evidence_and_non_pass_evidence_remain_new_but_inspectable() -> None:
    assert summarize(()).state is LearnerState.NEW
    result = summarize(
        (
            evidence("e1", LearnerState.EXPLAINED, outcome=EvidenceOutcome.PARTIAL),
            evidence("e2", LearnerState.APPLIED, outcome=EvidenceOutcome.FAIL),
            evidence("e3", LearnerState.TRANSFERRED, outcome=EvidenceOutcome.INSUFFICIENT_EVIDENCE),
        )
    )
    assert result.state is LearnerState.NEW
    assert result.supporting_evidence_ids == ()
    assert result.excluded_evidence_ids == ("e1", "e2", "e3")


@pytest.mark.parametrize(
    ("state", "transfer"),
    [
        (LearnerState.RECOGNIZED, False),
        (LearnerState.EXPLAINED, False),
        (LearnerState.APPLIED, False),
        (LearnerState.TRANSFERRED, True),
    ],
)
def test_each_pass_evidence_kind_reaches_its_state(state: LearnerState, transfer: bool) -> None:
    assert summarize((evidence("e1", state, transfer=transfer),)).state is state


def test_higher_quality_evidence_can_skip_elementary_stages() -> None:
    result = summarize((evidence("e1", LearnerState.TRANSFERRED, transfer=True),))
    assert result.state is LearnerState.TRANSFERRED


def test_configurable_thresholds_are_positive_non_decreasing_and_autonomous_at_least_two() -> None:
    assert AdvancementThresholds(1, 2, 3, 4, 5).transferred_passes == 4
    for values in ((0, 1, 1, 1, 2), (2, 1, 2, 2, 2), (1, 1, 1, 3, 2)):
        with pytest.raises(DomainValidationError, match="threshold"):
            AdvancementThresholds(*values)


def test_threshold_count_and_append_only_evidence_are_monotonic() -> None:
    config = AdvancementThresholds(1, 2, 2, 3, 3)
    first = summarize((evidence("e1", LearnerState.EXPLAINED),), config)
    second = summarize(
        (evidence("e1", LearnerState.EXPLAINED), evidence("e2", LearnerState.EXPLAINED)),
        config,
    )
    assert first.state is LearnerState.RECOGNIZED
    assert second.state is LearnerState.EXPLAINED


def test_wrong_version_and_scope_are_retained_but_excluded() -> None:
    wrong_version = evidence("e1", LearnerState.EXPLAINED, version=2)
    wrong_scope = evidence("e2", LearnerState.EXPLAINED, scope="rust")
    result = summarize((wrong_version, wrong_scope))
    assert result.state is LearnerState.NEW
    assert result.excluded_evidence_ids == ("e1", "e2")


def test_duplicate_evidence_ids_are_rejected() -> None:
    item = evidence("e1", LearnerState.RECOGNIZED)
    with pytest.raises(DomainValidationError, match="duplicate"):
        summarize((item, dataclasses.replace(item)))
