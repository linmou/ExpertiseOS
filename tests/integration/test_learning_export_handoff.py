#!/usr/bin/env python3
# Purpose: Verify actual C004 SQLite state through C007 export, restore, and deletion.

from __future__ import annotations

import dataclasses
import hashlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from expertiseos.domain.models import ApprovalReceipt, LearnerState, PendingOperationKind
from expertiseos.hosts.contract import DecisionAction, EventKind, HostEvent
from expertiseos.knowledge.backend import (
    IdempotencyConflictError,
    SearchQuery,
    VersionConflictError,
)
from expertiseos.learning.controls import (
    ApprovedKnowledgeRef,
    DeferredActivity,
    DeferredStatus,
    ExclusionKind,
    ScopeExclusion,
    default_daily_settings,
)
from expertiseos.learning.evidence import (
    AdvancementThresholds,
    AssistanceLevel,
    EvidenceOutcome,
    LearnerEvidence,
    approved_object_fact,
    validate_evidence,
)
from expertiseos.ownership import (
    ApprovedStateIdentityLookup,
    ApprovedStateRestoreTarget,
    BackendSnapshotSource,
    CollisionPolicy,
    CompositeSnapshotSource,
    DeletionScope,
    ExportScope,
    KnowledgeRef,
    OwnershipStatus,
    SelectionAuthority,
    SQLiteLearningDeletionTarget,
    SQLiteSnapshotSource,
    execute_delete,
    export_approved,
    plan_delete,
    restore_validated,
    validate_restore,
)
from expertiseos.state.sqlite import SQLiteState
from tests.backend_support import FakeBasicMemoryCli, approved, backend

NOW = datetime(2026, 9, 14, 12, tzinfo=UTC)


def _receipt(
    operation_id: str,
    kind: PendingOperationKind,
    refs: tuple[tuple[str, int], ...],
    offset: int,
) -> ApprovalReceipt:
    return ApprovalReceipt(
        operation_id,
        f"proposal-{operation_id}",
        kind,
        refs,
        "a" * 64,
        f"user-{operation_id}",
        "codex",
        NOW + timedelta(seconds=offset),
    )


def _user_event(event_id: str) -> HostEvent:
    return HostEvent(
        event_id,
        "codex",
        "session-export",
        EventKind.USER_INPUT,
        NOW,
        f"host-{event_id}",
        DecisionAction.SAVE,
    )


def test_actual_learning_state_round_trips_and_deletes_through_c007(tmp_path: Path) -> None:
    store = backend(tmp_path / "source-backend", FakeBasicMemoryCli())
    knowledge = store.create_approved(
        approved(
            "portable retry boundary",
            "python",
            ("procedure",),
            ("domain",),
            ("host-source",),
        ),
        "create-portable",
    )
    ref = (knowledge.id, knowledge.version)
    source = SQLiteState(tmp_path / "source.sqlite")
    evidence_receipt = source.record_receipt(
        _receipt("evidence-1", PendingOperationKind.LEARNING_EVIDENCE, (ref,), 1)
    )
    control_receipt = source.record_receipt(
        _receipt("control-1", PendingOperationKind.CONTROL_CHANGE, (), 2)
    )
    exclusion_receipt = source.record_receipt(
        _receipt("exclusion-1", PendingOperationKind.CONTROL_CHANGE, (), 3)
    )
    deferred_receipt = source.record_receipt(
        _receipt("deferred-1", PendingOperationKind.CONTROL_CHANGE, (ref,), 4)
    )

    search_result = store.search(SearchQuery("retry boundary", 1, "python", (), (), ()))[0]
    fact = approved_object_fact(search_result, "python")
    evidence = validate_evidence(
        LearnerEvidence(
            "learner-evidence-1",
            knowledge.id,
            knowledge.version,
            "task-1",
            "session-1",
            "explain retry behavior",
            EvidenceOutcome.PASS,
            AssistanceLevel.INDEPENDENT,
            "python",
            "user explanation",
            LearnerState.EXPLAINED,
            LearnerState.EXPLAINED,
            False,
            evidence_receipt.operation_id,
            NOW + timedelta(seconds=5),
        ),
        fact,
        evidence_receipt,
    )
    source.insert_evidence_once(evidence)
    settings = dataclasses.replace(
        default_daily_settings("UTC", 1),
        advancement_thresholds=AdvancementThresholds(2, 3, 4, 5, 6),
    )
    source.apply_control_change(0, settings, control_receipt.operation_id)
    exclusion = ScopeExclusion(
        "private-source",
        ExclusionKind.SOURCE,
        "source-private",
        NOW + timedelta(seconds=6),
        exclusion_receipt.operation_id,
    )
    source.replace_or_remove_exclusion(1, exclusion.id, exclusion, exclusion_receipt.operation_id)
    source.record_reflection_once("2026-09-14", "reflection-1")
    source.record_effort_once("2026-09-14", "effort-1", Decimal("2"))
    deferred = DeferredActivity(
        "deferred-activity-1",
        (ApprovedKnowledgeRef(*ref),),
        "explain_retry",
        NOW + timedelta(seconds=7),
        DeferredStatus.PENDING,
        deferred_receipt.operation_id,
    )
    source.insert_deferred_once(deferred)

    scope = ExportScope(
        (
            "knowledge",
            "source_reference",
            "approval_receipt",
            "learner_evidence",
            "control",
            "progress",
            "scope_exclusion",
            "deferred_activity",
        ),
        (KnowledgeRef(*ref),),
        (
            evidence_receipt.operation_id,
            control_receipt.operation_id,
            exclusion_receipt.operation_id,
            deferred_receipt.operation_id,
        ),
        ("2026-09-14",),
    )
    authority = SelectionAuthority(b"s" * 32, "codex", "session-export")
    destination = tmp_path / "learning-export"
    exported = export_approved(
        authority.issue_export(_user_event("export"), "export-1", scope, destination),
        scope,
        destination,
        CompositeSnapshotSource((BackendSnapshotSource(store), SQLiteSnapshotSource(source))),
        authority,
        "0.1.0",
        NOW,
    )

    assert exported.status is OwnershipStatus.COMMITTED
    assert dict(exported.record_counts) == {
        "knowledge": 1,
        "source_reference": 1,
        "approval_receipt": 4,
        "learner_evidence": 1,
        "control": 1,
        "progress": 1,
        "scope_exclusion": 1,
        "deferred_activity": 1,
    }

    restored_state = SQLiteState(tmp_path / "restored.sqlite")
    restored_store = backend(tmp_path / "restored-backend", FakeBasicMemoryCli())
    restore_plan = validate_restore(
        destination, ApprovedStateIdentityLookup(restored_store, restored_state, scope)
    )
    restored = restore_validated(
        restore_plan,
        authority.issue_restore(
            _user_event("restore"),
            "restore-1",
            restore_plan,
            CollisionPolicy.REJECT_DIVERGENT,
        ),
        authority,
        ApprovedStateRestoreTarget(restored_store, restored_state),
    )

    assert restored.status is OwnershipStatus.COMMITTED
    assert restored_store.get(knowledge.id, knowledge.version, include_retired=True) == knowledge
    assert restored_store.restore_approved((knowledge,), "restore-1") == (knowledge,)
    divergent = dataclasses.replace(
        knowledge,
        content="divergent content",
        content_digest=hashlib.sha256(b"divergent content").hexdigest(),
    )
    with pytest.raises(IdempotencyConflictError):
        restored_store.restore_approved((divergent,), "restore-1")
    with pytest.raises(VersionConflictError):
        restored_store.restore_approved((divergent,), "restore-collision")
    assert restored_state.list_evidence(knowledge.id, knowledge.version, "python", 20) == (
        evidence,
    )
    restored_settings = restored_state.read_control_state()
    assert restored_settings is not None
    assert restored_settings.version == 2
    assert restored_settings.advancement_thresholds == AdvancementThresholds(2, 3, 4, 5, 6)
    assert restored_state.read_period_progress("2026-09-14").effort_units == Decimal("2")
    assert restored_state.list_exclusions(20) == (exclusion,)
    assert restored_state.list_deferred(DeferredStatus.PENDING, 20) == (deferred,)

    delete_receipt = source.record_receipt(
        _receipt("delete-1", PendingOperationKind.DELETE, (ref,), 8)
    )
    deletion_plan = plan_delete(
        DeletionScope((KnowledgeRef(*ref),), True, True, True, ()), delete_receipt
    )
    deletion_target = SQLiteLearningDeletionTarget(source)
    deletion = execute_delete(deletion_plan, store, deletion_target)
    replayed_deletion = execute_delete(deletion_plan, store, deletion_target)

    assert deletion.status is OwnershipStatus.COMMITTED
    assert replayed_deletion.status is OwnershipStatus.COMMITTED
    assert store.get(knowledge.id, include_retired=True) is None
    assert source.list_evidence(knowledge.id, knowledge.version, None, 20) == ()
    assert source.list_deferred(None, 20) == ()
    source.close()
    restored_state.close()
