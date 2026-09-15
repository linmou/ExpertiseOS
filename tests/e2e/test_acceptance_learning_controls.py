#!/usr/bin/env python3
# Purpose: Test C004 AT-07 and AT-09 through AT-11 learner/control acceptance behavior.

from __future__ import annotations

import dataclasses
from datetime import timedelta
from decimal import Decimal

from expertiseos.domain.models import LearnerState, PendingOperationKind
from expertiseos.learning.controls import (
    ControlReason,
    PeriodProgress,
    default_daily_settings,
    resolve_controls,
)
from expertiseos.learning.evidence import (
    AdvancementThresholds,
    ApprovedObjectFact,
    AssistanceLevel,
    EvidenceOutcome,
    LearnerEvidence,
    summarize_mastery,
    validate_evidence,
)
from expertiseos.state.sqlite import SQLiteState
from tests.consent_support import NOW
from tests.integration.test_learning_state_sqlite import _authorize_receipt


def _evidence(
    identifier: str,
    receipt_id: str,
    outcome: EvidenceOutcome,
    task_ref: str,
    session_id: str,
    transfer: bool,
) -> LearnerEvidence:
    return LearnerEvidence(
        identifier,
        "knowledge-learning",
        1,
        task_ref,
        session_id,
        "apply the retry boundary",
        outcome,
        AssistanceLevel.INDEPENDENT,
        "python",
        "my approved reasoning",
        LearnerState.TRANSFERRED,
        LearnerState.TRANSFERRED,
        transfer,
        receipt_id,
        NOW,
    )


def test_at07_only_persisted_pass_evidence_advances_numeric_mastery() -> None:
    state = SQLiteState(":memory:")
    fact = ApprovedObjectFact("knowledge-learning", 1, "python", False)
    outcomes = (EvidenceOutcome.PARTIAL, EvidenceOutcome.FAIL, EvidenceOutcome.PASS)
    records: list[LearnerEvidence] = []
    for index, outcome in enumerate(outcomes):
        receipt = _authorize_receipt(
            state,
            PendingOperationKind.LEARNING_EVIDENCE,
            f"at07-{outcome.value}",
            ((fact.knowledge_id, fact.knowledge_version),),
            f"AT-07 {outcome.value}",
            index * 10 + 1,
        )
        record = validate_evidence(
            _evidence(
                f"evidence-{outcome.value}",
                receipt.operation_id,
                outcome,
                f"task-{index}",
                f"session-{index}",
                outcome is EvidenceOutcome.PASS,
            ),
            fact,
            receipt,
        )
        records.append(state.insert_evidence_once(record))
    summary = summarize_mastery(
        fact,
        tuple(records),
        AdvancementThresholds(1, 2, 2, 2, 2),
        False,
        NOW + timedelta(hours=1),
    )
    assert summary.state is LearnerState.RECOGNIZED
    assert summary.supporting_evidence_ids == ("evidence-pass",)
    assert set(summary.excluded_evidence_ids) == {
        "evidence-partial",
        "evidence-fail",
    }
    state.close()


def test_at09_autonomous_requires_every_non_numeric_safeguard() -> None:
    fact = ApprovedObjectFact("knowledge-learning", 1, "python", False)
    first = _evidence(
        "evidence-one", "receipt-one", EvidenceOutcome.PASS, "task-one", "session-one", True
    )
    second = _evidence(
        "evidence-two", "receipt-two", EvidenceOutcome.PASS, "task-two", "session-two", False
    )
    thresholds = AdvancementThresholds(1, 1, 1, 1, 2)
    complete = summarize_mastery(fact, (first, second), thresholds, True, NOW + timedelta(hours=1))
    no_agreement = summarize_mastery(
        fact, (first, second), thresholds, False, NOW + timedelta(hours=1)
    )
    contradiction = summarize_mastery(
        dataclasses.replace(fact, unresolved_relevant_contradiction=True),
        (first, second),
        thresholds,
        True,
        NOW + timedelta(hours=1),
    )
    assert complete.state is LearnerState.AUTONOMOUS
    assert no_agreement.state is LearnerState.TRANSFERRED
    assert contradiction.state is LearnerState.TRANSFERRED


def test_at10_target_and_fatigue_have_distinct_precedence_and_effects() -> None:
    settings = default_daily_settings("UTC", 1)
    progress = PeriodProgress("2026-09-14", 0, Decimal("0"), (), ())
    resting = dataclasses.replace(settings, fatigue_rest_until=NOW + timedelta(minutes=60))
    fatigue = resolve_controls(resting, progress, NOW)
    target = resolve_controls(
        settings,
        dataclasses.replace(progress, reflection_count=settings.reflection_target),
        NOW,
    )
    assert fatigue.reason is ControlReason.FATIGUE_REST
    assert fatigue.approved_recall is True
    assert fatigue.observe is False
    assert target.reason is ControlReason.TARGET_SATISFIED
    assert target.observe is True
    assert target.proactive_exercises is False


def test_at11_pause_preserves_recall_while_disable_stops_all_expertiseos_activity() -> None:
    settings = default_daily_settings("UTC", 1)
    progress = PeriodProgress("2026-09-14", 0, Decimal("0"), (), ())
    paused = resolve_controls(dataclasses.replace(settings, learning_paused=True), progress, NOW)
    disabled = resolve_controls(dataclasses.replace(settings, enabled=False), progress, NOW)
    assert paused.reason is ControlReason.PAUSED
    assert paused.approved_recall is True
    assert (paused.observe, paused.prompt_collection, paused.proactive_exercises) == (
        False,
        False,
        False,
    )
    assert disabled.reason is ControlReason.DISABLED
    assert (
        disabled.observe,
        disabled.prompt_collection,
        disabled.proactive_exercises,
        disabled.approved_recall,
    ) == (False, False, False, False)
