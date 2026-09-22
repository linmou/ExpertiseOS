#!/usr/bin/env python3
# Purpose: Verify E08 passes actual C004 learning and control outputs through C008.

from __future__ import annotations

import dataclasses
from datetime import timedelta
from pathlib import Path
from typing import cast

from expertiseos.domain.models import LearnerState, PendingOperationKind
from expertiseos.hosts.contract import DecisionAction, DecisionObservation, DecisionRejection
from expertiseos.knowledge.backend import SearchQuery
from expertiseos.learning.controls import ControlReason, ControlResolution, default_daily_settings
from expertiseos.learning.evidence import (
    AdvancementThresholds,
    AssistanceLevel,
    EvidenceOutcome,
    LearnerEvidence,
    LearningInspection,
    approved_object_fact,
)
from expertiseos.service import ExpertiseOSService, ToolStatus
from tests.backend_support import approved
from tests.consent_support import NOW
from tests.integration.product_handoff_support import (
    ProductHandoffGraph,
    build_product_handoff_graph,
)
from tests.integration.test_learning_state_sqlite import _authorize_receipt


def _grant(graph: ProductHandoffGraph, proposal_id: str, grant_id: str) -> None:
    graph.knowledge.register_decision(
        proposal_id,
        grant_id,
        DecisionObservation(
            True,
            DecisionAction.SAVE,
            f"actual-user:{proposal_id}",
            DecisionRejection.NONE,
        ),
        NOW + timedelta(seconds=1),
    )


def test_actual_c004_results_feed_c008_learning_and_control_reads(tmp_path: Path) -> None:
    graph = build_product_handoff_graph(tmp_path)
    try:
        facade = ExpertiseOSService(graph.knowledge, graph.backend, graph.state, ())
        record = graph.backend.create_approved(
            approved("explain the retry boundary", "python", ("fact",), ("domain",), ("e08",)),
            "e08-create",
        )
        retrieved = graph.backend.search(SearchQuery("retry boundary", 1, "python", (), (), ()))[0]
        fact = approved_object_fact(retrieved, "python")
        for identifier, outcome in (
            ("e08-partial", EvidenceOutcome.PARTIAL),
            ("e08-pass", EvidenceOutcome.PASS),
        ):
            evidence = LearnerEvidence(
                identifier,
                record.id,
                record.version,
                f"task:{identifier}",
                f"session:{identifier}",
                "apply the retry boundary",
                outcome,
                AssistanceLevel.INDEPENDENT,
                "python",
                "actual user response",
                LearnerState.RECOGNIZED,
                LearnerState.RECOGNIZED,
                False,
                f"operation:{identifier}",
                NOW,
            )
            proposed = facade.propose_learning_evidence(
                f"proposal:{identifier}",
                evidence.approval_receipt_id,
                evidence.session_id,
                "codex",
                evidence,
                {record.id: record.version},
                NOW,
            )
            assert proposed.status is ToolStatus.OK
            _grant(graph, f"proposal:{identifier}", f"grant:{identifier}")
            committed = facade.commit_proposal(
                f"proposal:{identifier}",
                f"grant:{identifier}",
                evidence.approval_receipt_id,
                {record.id: record.version},
            )
            assert committed.status is ToolStatus.COMMITTED

        learning = facade.inspect_learning_state(
            fact,
            AdvancementThresholds(1, 2, 2, 2, 2),
            False,
            NOW + timedelta(minutes=1),
        )
        inspection = cast(LearningInspection, learning.data)
        assert learning.status is ToolStatus.OK
        assert inspection.summary.state is LearnerState.RECOGNIZED
        assert inspection.summary.supporting_evidence_ids == ("e08-pass",)
        assert "e08-partial" in inspection.summary.excluded_evidence_ids

        initial = default_daily_settings("UTC", 1)
        receipt = _authorize_receipt(
            graph.state,
            PendingOperationKind.CONTROL_CHANGE,
            "e08-control-seed",
            (("control-state", 1),),
            "seed controls",
            300,
        )
        graph.state.apply_control_change(0, initial, receipt.operation_id)
        paused = dataclasses.replace(initial, learning_paused=True, version=2)
        facade.propose_control_change(
            "e08-control-proposal",
            "e08-control-operation",
            "e08-control-session",
            "codex",
            paused,
            {"control-state": 1},
            NOW,
        )
        _grant(graph, "e08-control-proposal", "e08-control-grant")
        assert (
            facade.commit_proposal(
                "e08-control-proposal",
                "e08-control-grant",
                "e08-control-operation",
                {"control-state": 1},
            ).status
            is ToolStatus.COMMITTED
        )
        controls = facade.inspect_controls("2026-09-14", NOW)
        assert controls.status is ToolStatus.OK
        assert cast(ControlResolution, controls.data).reason is ControlReason.PAUSED
    finally:
        graph.state.close()
