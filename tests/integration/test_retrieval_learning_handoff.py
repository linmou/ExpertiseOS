#!/usr/bin/env python3
# Purpose: Test an actual C003 retrieval result through C004 validation and inspection.

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from expertiseos.domain.models import LearnerState, PendingOperationKind
from expertiseos.knowledge.backend import SearchQuery
from expertiseos.learning.evidence import (
    AdvancementThresholds,
    EvidenceOutcome,
    approved_object_fact,
    inspect_learning_state,
    summarize_mastery,
    validate_evidence,
)
from expertiseos.state.sqlite import SQLiteState
from tests.backend_support import FakeBasicMemoryCli, approved, backend
from tests.consent_support import NOW
from tests.integration.test_learning_state_sqlite import _authorize_receipt, _evidence

pytestmark = pytest.mark.integration


def test_c003_retrieval_facts_are_consumed_by_c004_validation_and_inspection(
    tmp_path: Path,
) -> None:
    store = backend(tmp_path / "backend", FakeBasicMemoryCli())
    record = store.create_approved(
        approved(
            "transfer retry knowledge",
            "python",
            ("procedure",),
            ("domain",),
            ("host-user-e04",),
        ),
        "operation-knowledge-e04",
    )
    retrieval = store.search(SearchQuery("transfer retry", 1, "python", (), (), ()))[0]
    fact = approved_object_fact(retrieval, "python")
    state = SQLiteState(":memory:")
    receipt = _authorize_receipt(
        state,
        PendingOperationKind.LEARNING_EVIDENCE,
        "operation-e04",
        ((record.id, record.version),),
        "retrieved object explanation",
        1,
    )
    evidence = validate_evidence(
        _evidence(
            "evidence-e04",
            EvidenceOutcome.PASS,
            receipt.operation_id,
            record.id,
            record.version,
            10,
        ),
        fact,
        receipt,
    )
    summary = summarize_mastery(
        fact,
        (evidence,),
        AdvancementThresholds(1, 1, 1, 1, 2),
        False,
        NOW + timedelta(hours=1),
    )
    inspection = inspect_learning_state(summary, (evidence,), 20)

    assert fact.knowledge_id == retrieval.knowledge_id == record.id
    assert fact.knowledge_version == retrieval.version == record.version
    assert summary.state is LearnerState.EXPLAINED
    assert inspection.supporting_evidence == (evidence,)
    state.close()
