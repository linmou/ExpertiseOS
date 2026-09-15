#!/usr/bin/env python3
# Purpose: Test a real C002 approval receipt through C004 evidence persistence and summary.

from __future__ import annotations

from datetime import timedelta

import pytest

from expertiseos.domain.models import LearnerState, PendingOperationKind
from expertiseos.learning.evidence import (
    AdvancementThresholds,
    ApprovedObjectFact,
    EvidenceOutcome,
    summarize_mastery,
    validate_evidence,
)
from expertiseos.state.sqlite import SQLiteState
from tests.consent_support import NOW
from tests.integration.test_learning_state_sqlite import _authorize_receipt, _evidence

pytestmark = pytest.mark.integration


def test_c002_approved_evidence_is_the_record_persisted_and_summarized() -> None:
    state = SQLiteState(":memory:")
    fact = ApprovedObjectFact("knowledge-e03", 1, "python", False)
    receipt = _authorize_receipt(
        state,
        PendingOperationKind.LEARNING_EVIDENCE,
        "operation-e03",
        ((fact.knowledge_id, fact.knowledge_version),),
        "approved learner explanation",
        1,
    )
    evidence = validate_evidence(
        _evidence(
            "evidence-e03",
            EvidenceOutcome.PASS,
            receipt.operation_id,
            fact.knowledge_id,
            fact.knowledge_version,
            10,
        ),
        fact,
        receipt,
    )

    stored = state.insert_evidence_once(evidence)
    persisted = state.list_evidence(fact.knowledge_id, fact.knowledge_version, "python", 20)
    summary = summarize_mastery(
        fact,
        persisted,
        AdvancementThresholds(1, 1, 1, 1, 2),
        False,
        NOW + timedelta(hours=1),
    )

    assert stored == evidence
    assert persisted == (evidence,)
    assert summary.state is LearnerState.EXPLAINED
    assert summary.supporting_evidence_ids == (evidence.id,)
    state.close()
