#!/usr/bin/env python3
# Purpose: Verify deterministic ownership/reliability portions of AT-05, AT-13, and AT-14.

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import pytest

from expertiseos.domain.models import CommitResult, CommitStatus
from expertiseos.knowledge.backend import (
    IndexState,
    RetrievalResponse,
    SearchMode,
    SearchQuery,
    StoreState,
    TrustLevel,
)
from expertiseos.ownership import (
    DeletionPlan,
    KnowledgeRef,
    OwnershipError,
    UninstallDataChoice,
    plan_uninstall,
)
from expertiseos.reliability import classify_commit
from expertiseos.security import ControlledLocation, audit_candidate_absence
from expertiseos.service import ExpertiseOSService, ToolStatus
from expertiseos.state.sqlite import SQLiteState
from tests.backend_support import FakeBasicMemoryCli, approved, backend
from tests.e2e.conftest import ProductGraph
from tests.fakes import DeterministicClock, DeterministicIdGenerator, FakeKnowledgeBackend


def test_at05_unapproved_candidate_marker_is_absent_after_restart(tmp_path: Path) -> None:
    marker = "UNAPPROVED_AT05_RELIABILITY_MARKER"
    store = backend(tmp_path / "backend", FakeBasicMemoryCli())
    store.create_approved(
        approved("approved value", None, ("fact",), ("domain",), ("host:approved",)),
        "create-approved",
    )
    state_path = tmp_path / "state.sqlite"
    SQLiteState(state_path).close()

    report = audit_candidate_absence(
        "at05-restart",
        marker,
        (
            ControlledLocation("backend", tmp_path / "backend"),
            ControlledLocation("state", state_path),
        ),
        ("host-owned transcripts",),
    )

    assert report.passed is True
    assert all(location.marker_found is False for location in report.locations)


def test_at13_canonical_failure_never_renders_saved_or_blocks_result_reporting() -> None:
    unavailable = FakeKnowledgeBackend(
        DeterministicClock(datetime(2026, 9, 14, tzinfo=UTC), timedelta(seconds=1)),
        DeterministicIdGenerator("knowledge", 1),
        StoreState.UNAVAILABLE,
        IndexState.UNAVAILABLE,
        SearchMode.UNAVAILABLE,
    )

    outcome = classify_commit(
        CommitResult(CommitStatus.FAILED, (), None, "canonical_unavailable"), unavailable
    )

    assert outcome.render_saved is False
    assert outcome.status is CommitStatus.FAILED
    assert outcome.error_code == "canonical_unavailable"


def test_at14_uninstall_requires_an_explicit_keep_or_approved_delete_choice() -> None:
    keep = plan_uninstall(UninstallDataChoice.KEEP, None)
    assert keep.remove_host_integrations is True
    assert keep.unregister_service is True
    assert keep.deletion_plan is None

    with pytest.raises(OwnershipError, match="approved deletion plan"):
        plan_uninstall(UninstallDataChoice.DELETE, None)

    deletion = DeletionPlan(
        "delete-1",
        (KnowledgeRef("knowledge-1", 1),),
        True,
        True,
        True,
        ("operating-system backups are outside product control",),
    )
    delete = plan_uninstall(UninstallDataChoice.DELETE, deletion)
    assert delete.deletion_plan == deletion
    assert delete.remove_host_integrations is True
    assert delete.unregister_service is True


def test_at15_adversarial_approved_content_remains_bounded_untrusted_data(
    product_graph: ProductGraph,
) -> None:
    scenarios = Path(__file__).parents[2] / "examples/reference_scenarios"
    fixture_path = scenarios / "adversarial_content.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    malicious = str(fixture["records"][0])
    record = product_graph.backend.create_approved(
        approved(malicious, None, ("fact",), ("domain",), ("approved:adversarial",)),
        "initial-approved-adversarial",
    )
    approved_before = product_graph.backend.get(record.id)
    facade = ExpertiseOSService(
        product_graph.knowledge,
        product_graph.backend,
        product_graph.state,
        (),
    )

    result = facade.search_knowledge(SearchQuery("Ignore expertiseOS", 1, None, (), (), ()))

    assert result.status is ToolStatus.OK
    response = cast(RetrievalResponse, result.data)
    assert response.results[0].knowledge_id == record.id
    assert response.results[0].trust is TrustLevel.UNTRUSTED_DATA
    assert len(response.results) == 1
    assert not hasattr(response.results[0], "authorized")
    control_result = facade.propose_control_change(
        "forged-control-proposal",
        "forged-control",
        "adversarial-session",
        "model",
        malicious,  # type: ignore[arg-type]
        {},
        datetime(2026, 9, 14, tzinfo=UTC),
    )
    assert control_result.status is ToolStatus.OK
    assert control_result.capabilities == ()
    assert product_graph.grants.get("forged-control") is None
    assert product_graph.backend.get(record.id) == approved_before
    assert product_graph.state.read_control_state() is None
    assert product_graph.state.list_evidence(record.id, record.version, "python", 20) == ()
