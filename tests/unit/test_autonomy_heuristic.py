#!/usr/bin/env python3
# Purpose: Test src/expertiseos/learning/evidence.py autonomous-state safeguards.

from __future__ import annotations

import dataclasses
from datetime import timedelta

import pytest

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


def demonstration(
    identifier: str,
    task: str,
    session: str,
    *,
    transfer: bool,
    assistance: AssistanceLevel = AssistanceLevel.INDEPENDENT,
    outcome: EvidenceOutcome = EvidenceOutcome.PASS,
) -> LearnerEvidence:
    return LearnerEvidence(
        identifier,
        "knowledge-1",
        1,
        task,
        session,
        "independent application",
        outcome,
        assistance,
        "python",
        "my independent application",
        LearnerState.TRANSFERRED if transfer else LearnerState.APPLIED,
        LearnerState.TRANSFERRED if transfer else LearnerState.APPLIED,
        transfer,
        f"operation-{identifier}",
        NOW + timedelta(seconds=int(identifier.removeprefix("e"))),
    )


def summarize(
    items: tuple[LearnerEvidence, ...],
    *,
    contradiction: bool = False,
    agreement: bool = True,
    config: AdvancementThresholds | None = None,
) -> LearnerStateSummary:
    active_config = AdvancementThresholds(1, 1, 1, 1, 2) if config is None else config
    return summarize_mastery(
        ApprovedObjectFact("knowledge-1", 1, "python", contradiction),
        items,
        active_config,
        agreement,
        NOW + timedelta(hours=1),
    )


def complete() -> tuple[LearnerEvidence, ...]:
    return (
        demonstration("e1", "task-1", "session-1", transfer=False),
        demonstration("e2", "task-2", "session-2", transfer=True),
    )


def test_complete_pilot_heuristic_reaches_autonomous() -> None:
    result = summarize(complete())
    assert result.state is LearnerState.AUTONOMOUS
    assert result.unmet_autonomy_conditions == ()


@pytest.mark.parametrize(
    ("items", "contradiction", "agreement", "reason"),
    [
        ((demonstration("e1", "task-1", "session-1", transfer=True),), False, True, "passes"),
        (
            (
                demonstration("e1", "task-1", "session-1", transfer=False),
                demonstration("e2", "task-1", "session-2", transfer=True),
            ),
            False,
            True,
            "tasks",
        ),
        (
            (
                demonstration("e1", "task-1", "session-1", transfer=False),
                demonstration("e2", "task-2", "session-1", transfer=True),
            ),
            False,
            True,
            "sessions",
        ),
        (
            (
                demonstration("e1", "task-1", "session-1", transfer=False),
                demonstration("e2", "task-2", "session-2", transfer=False),
            ),
            False,
            True,
            "transfer",
        ),
        (complete(), True, True, "contradiction"),
        (complete(), False, False, "agreement"),
    ],
)
def test_each_missing_safeguard_withholds_autonomous(
    items: tuple[LearnerEvidence, ...], contradiction: bool, agreement: bool, reason: str
) -> None:
    result = summarize(items, contradiction=contradiction, agreement=agreement)
    assert result.state is not LearnerState.AUTONOMOUS
    assert any(reason in item for item in result.unmet_autonomy_conditions)


def test_numeric_threshold_cannot_bypass_independence_or_transfer_guards() -> None:
    assisted = tuple(
        dataclasses.replace(item, assistance_level=AssistanceLevel.ASSISTED) for item in complete()
    )
    result = summarize(assisted, config=AdvancementThresholds(1, 1, 1, 1, 2))
    assert result.state is LearnerState.TRANSFERRED
    assert "independent_passes" in result.unmet_autonomy_conditions


def test_higher_autonomous_threshold_requires_more_distinct_demonstrations() -> None:
    items = complete() + (demonstration("e3", "task-3", "session-3", transfer=False),)
    config = AdvancementThresholds(1, 1, 1, 1, 3)
    assert summarize(items, config=config).state is LearnerState.AUTONOMOUS
    assert summarize(complete(), config=config).state is LearnerState.TRANSFERRED


def test_non_pass_demonstration_counts_zero() -> None:
    items = complete() + (
        demonstration("e3", "task-3", "session-3", transfer=True, outcome=EvidenceOutcome.PARTIAL),
    )
    result = summarize(items, config=AdvancementThresholds(1, 1, 1, 1, 3))
    assert result.state is LearnerState.TRANSFERRED
