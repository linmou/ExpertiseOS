#!/usr/bin/env python3
# Purpose: Verify deterministic ownership/reliability portions of AT-05, AT-13, and AT-14.

from __future__ import annotations

import json
import socket
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import pytest

from expertiseos.domain.models import ApprovalReceipt, CommitResult, CommitStatus
from expertiseos.knowledge.backend import (
    IndexState,
    RetrievalResponse,
    SearchMode,
    SearchQuery,
    StoreState,
    TrustLevel,
)
from expertiseos.ownership import (
    ApprovedStateIdentityLookup,
    ApprovedStateRestoreTarget,
    BackendSnapshotSource,
    CollisionPolicy,
    CompositeSnapshotSource,
    DeletionPlan,
    DeletionScope,
    ExportScope,
    KnowledgeRef,
    OwnershipError,
    SelectionAuthority,
    UninstallDataChoice,
    plan_uninstall,
    validate_restore,
)
from expertiseos.reliability import (
    OperationKind,
    OperationRecord,
    OperationStatus,
    classify_commit,
    recover_approved_state,
)
from expertiseos.security import ControlledLocation, audit_candidate_absence
from expertiseos.service import ExpertiseOSService, ToolStatus
from expertiseos.state.sqlite import SQLiteState
from tests.backend_support import FakeBasicMemoryCli, approved, backend
from tests.consent_support import NOW, observation
from tests.e2e.conftest import ProductGraph
from tests.fakes import DeterministicClock, DeterministicIdGenerator, FakeKnowledgeBackend
from tests.integration.fixtures.reliability_fixtures import user_event


class _UnusedReceiptReconciler:
    def reconcile_receipt(self, operation_id: str) -> ApprovalReceipt:
        raise AssertionError(f"unexpected receipt reconciliation: {operation_id}")


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


def test_at13_index_outage_falls_back_then_recovers(product_graph: ProductGraph) -> None:
    record = product_graph.backend.create_approved(
        approved("recoverable local keyword", None, ("fact",), ("domain",), ("host:at13",)),
        "create-at13",
    )
    facade = ExpertiseOSService(
        product_graph.knowledge,
        product_graph.backend,
        product_graph.state,
        (),
    )
    product_graph.cli.fail_search = True

    degraded = facade.search_knowledge(SearchQuery("recoverable", 1, None, (), (), ()))

    assert degraded.status is ToolStatus.DEGRADED
    response = cast(RetrievalResponse, degraded.data)
    assert response.results[0].knowledge_id == record.id
    assert response.mode is SearchMode.KEYWORD
    assert response.index_state is IndexState.DEGRADED
    product_graph.cli.fail_search = False
    recovery = recover_approved_state(
        (
            OperationRecord(
                "rebuild-at13",
                OperationKind.INDEX_REBUILD,
                (),
                OperationStatus.PENDING,
            ),
        ),
        product_graph.state,
        _UnusedReceiptReconciler(),
        product_graph.backend,
    )
    assert recovery.committed_operations == ("rebuild-at13",)
    assert recovery.incomplete_operations == ()
    assert facade.health().status is ToolStatus.OK


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


def test_at14_guarded_export_restore_delete_round_trip(
    product_graph: ProductGraph, tmp_path: Path
) -> None:
    record = product_graph.backend.create_approved(
        approved("portable ownership value", None, ("fact",), ("domain",), ("host:at14",)),
        "create-at14",
    )
    facade = ExpertiseOSService(
        product_graph.knowledge,
        product_graph.backend,
        product_graph.state,
        (),
    )
    scope = ExportScope(("knowledge",), (KnowledgeRef(record.id, record.version),), (), ())
    authority = SelectionAuthority(b"at14-selection-authority-secret!", "adapter-1", "session-1")
    destination = tmp_path / "export-at14"
    exported = facade.export_data(
        authority.issue_export(
            user_event("export-at14"), "export-operation-at14", scope, destination
        ),
        scope,
        destination,
        CompositeSnapshotSource((BackendSnapshotSource(product_graph.backend),)),
        authority,
        "0.1.0",
        NOW,
    )
    assert exported.status is ToolStatus.COMMITTED

    restored_backend = backend(tmp_path / "restored-backend", FakeBasicMemoryCli())
    restored_state = SQLiteState(tmp_path / "restored-state.sqlite")
    plan = validate_restore(
        destination,
        ApprovedStateIdentityLookup(restored_backend, restored_state, scope),
    )
    restored = facade.restore_data(
        plan,
        authority.issue_restore(
            user_event("restore-at14"),
            "restore-operation-at14",
            plan,
            CollisionPolicy.REJECT_DIVERGENT,
        ),
        authority,
        ApprovedStateRestoreTarget(restored_backend, restored_state),
    )
    assert restored.status is ToolStatus.COMMITTED
    assert restored_backend.get(record.id) == record

    deletion_scope = DeletionScope(
        (KnowledgeRef(record.id, record.version),),
        True,
        True,
        True,
        ("operating-system backups remain outside product control",),
    )
    proposed = facade.propose_retire_or_delete(
        "delete-proposal-at14",
        "delete-operation-at14",
        "session-at14",
        "codex",
        deletion_scope,
        {record.id: record.version},
        NOW,
    )
    assert proposed.status is ToolStatus.OK
    product_graph.knowledge.register_decision(
        "delete-proposal-at14",
        "delete-grant-at14",
        observation(user_event_ref="host:delete-at14"),
        NOW + timedelta(seconds=1),
    )
    deleted = facade.commit_proposal(
        "delete-proposal-at14",
        "delete-grant-at14",
        "delete-operation-at14",
        {record.id: record.version},
    )
    assert deleted.status is ToolStatus.COMMITTED
    assert product_graph.backend.get(record.id, record.version, True) is None
    assert deletion_scope.external_limits == (
        "operating-system backups remain outside product control",
    )
    restored_state.close()


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


def test_at16_runtime_is_offline_and_uses_local_keyword_fallback(
    product_graph: ProductGraph, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempts: list[object] = []

    def deny_connect(self: socket.socket, address: object) -> None:
        attempts.append(address)
        raise AssertionError("outbound network attempted")

    monkeypatch.setattr(socket.socket, "connect", deny_connect)
    record = product_graph.backend.create_approved(
        approved("offline fallback value", None, ("fact",), ("domain",), ("host:at16",)),
        "create-at16",
    )
    product_graph.cli.fail_search = True
    facade = ExpertiseOSService(
        product_graph.knowledge,
        product_graph.backend,
        product_graph.state,
        (),
    )

    result = facade.search_knowledge(SearchQuery("offline", 1, None, (), (), ()))

    assert result.status is ToolStatus.DEGRADED
    response = cast(RetrievalResponse, result.data)
    assert response.results[0].knowledge_id == record.id
    assert response.mode is SearchMode.KEYWORD
    assert attempts == []
