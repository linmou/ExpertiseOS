#!/usr/bin/env python3
# Purpose: Test C004 learning records through C002 SQLite state and C003 object facts.

from __future__ import annotations

import dataclasses
import hashlib
import sqlite3
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from expertiseos.approval.gate import (
    ApprovalGate,
    DecisionGrantStore,
    canonical_approval_digest,
)
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.domain.errors import DomainValidationError, ReceiptConflictError, StaleVersionError
from expertiseos.domain.models import (
    ApprovalReceipt,
    CandidateState,
    CreateOperation,
    LearnerState,
    PendingOperation,
    PendingOperationKind,
)
from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionBinding,
    EventKind,
    HostEvent,
)
from expertiseos.knowledge.backend import ApprovedKnowledgeInput, SearchQuery
from expertiseos.learning.controls import (
    ApprovedKnowledgeRef,
    DeferredActivity,
    DeferredStatus,
    ExclusionKind,
    ScopeExclusion,
    default_daily_settings,
    remove_deferred,
)
from expertiseos.learning.evidence import (
    AdvancementThresholds,
    AssistanceLevel,
    EvidenceOutcome,
    LearnerEvidence,
    approved_object_fact,
    summarize_mastery,
    validate_evidence,
)
from expertiseos.state.sqlite import SQLiteState
from tests.backend_support import FakeBasicMemoryCli, approved, backend
from tests.consent_support import NOW
from tests.fakes import FakeHostAdapter

pytestmark = pytest.mark.integration


def _approval_payload(semantic_text: str) -> CreateOperation:
    return CreateOperation(
        ApprovedKnowledgeInput(
            semantic_text,
            hashlib.sha256(semantic_text.encode("utf-8")).hexdigest(),
            ("state_change",),
            ("self",),
            None,
            "approved",
            ("integration:e03",),
            "user",
        )
    )


def _authorize_receipt(
    state: SQLiteState,
    kind: PendingOperationKind,
    operation_id: str,
    object_refs: tuple[tuple[str, int], ...],
    semantic_text: str,
    offset_seconds: int,
) -> ApprovalReceipt:
    payload = _approval_payload(semantic_text)
    expected_versions = tuple(sorted(object_refs))
    digest = canonical_approval_digest(kind, payload, expected_versions)
    proposal = PendingOperation(
        f"proposal-{operation_id}",
        operation_id,
        f"session-{operation_id}",
        "codex",
        kind,
        CandidateState.DETECTED,
        payload,
        digest,
        expected_versions,
        NOW + timedelta(seconds=offset_seconds),
    )
    candidates = CandidateStore()
    candidates.create_detected(proposal)
    candidates.mark_awaiting_checkpoint(proposal.proposal_id)
    proposal = candidates.mark_awaiting_decision(proposal.proposal_id)
    host = FakeHostAdapter(proposal.adapter_id, proposal.session_id, ())
    host.on_session_start(
        HostEvent(
            f"start-{operation_id}",
            proposal.adapter_id,
            proposal.session_id,
            EventKind.SESSION_START,
            NOW + timedelta(seconds=offset_seconds + 1),
            None,
            None,
        )
    )
    event = HostEvent(
        f"event-{operation_id}",
        proposal.adapter_id,
        proposal.session_id,
        EventKind.USER_INPUT,
        NOW + timedelta(seconds=offset_seconds + 2),
        f"user-{operation_id}",
        DecisionAction.SAVE,
    )
    host.on_user_event(event)
    observation = host.register_decision_if_unambiguous(
        event,
        DecisionBinding(
            proposal.proposal_id,
            proposal.kind.value,
            proposal.adapter_id,
            proposal.session_id,
            proposal.content_digest,
            proposal.expected_versions,
            (DecisionAction.SAVE,),
        ),
    )
    grants = DecisionGrantStore()
    grant = grants.register(
        proposal,
        observation,
        f"grant-{operation_id}",
        NOW + timedelta(seconds=offset_seconds + 3),
    )
    ApprovalGate().validate(
        proposal,
        grant,
        operation_id,
        dict(expected_versions),
        False,
    )
    grants.consume(grant.grant_id, NOW + timedelta(seconds=offset_seconds + 4))
    receipt = ApprovalReceipt(
        operation_id,
        proposal.proposal_id,
        kind,
        object_refs,
        digest,
        observation.user_event_ref or "",
        proposal.adapter_id,
        NOW + timedelta(seconds=offset_seconds + 5),
    )
    return state.record_receipt(receipt)


def _evidence(
    identifier: str,
    outcome: EvidenceOutcome,
    receipt_id: str,
    knowledge_id: str,
    version: int,
    offset_seconds: int,
) -> LearnerEvidence:
    return LearnerEvidence(
        identifier,
        knowledge_id,
        version,
        f"task-{identifier}",
        f"session-{identifier}",
        "explain the retry boundary",
        outcome,
        AssistanceLevel.INDEPENDENT,
        "python",
        "my approved explanation",
        LearnerState.EXPLAINED,
        LearnerState.EXPLAINED,
        False,
        receipt_id,
        NOW + timedelta(seconds=offset_seconds),
    )


def test_actual_approved_evidence_persists_restarts_and_uses_numeric_thresholds(
    tmp_path: Path,
) -> None:
    database = tmp_path / "state.sqlite3"
    state = SQLiteState(database)
    store = backend(tmp_path / "backend", FakeBasicMemoryCli())
    record = store.create_approved(
        approved(
            "authorized learning boundary",
            "python",
            ("procedure",),
            ("domain",),
            ("host-user-learning",),
        ),
        "knowledge-learning",
    )
    result = store.search(SearchQuery("learning boundary", 1, "python", (), (), ()))[0]
    fact = approved_object_fact(result, "python")

    partial_receipt = _authorize_receipt(
        state,
        PendingOperationKind.LEARNING_EVIDENCE,
        "evidence-partial",
        ((record.id, record.version),),
        "partial evidence",
        10,
    )
    pass_receipt = _authorize_receipt(
        state,
        PendingOperationKind.LEARNING_EVIDENCE,
        "evidence-pass",
        ((record.id, record.version),),
        "passing evidence",
        20,
    )
    partial = validate_evidence(
        _evidence(
            "partial-1", EvidenceOutcome.PARTIAL, partial_receipt.operation_id, record.id, 1, 30
        ),
        fact,
        partial_receipt,
    )
    passed = validate_evidence(
        _evidence("pass-1", EvidenceOutcome.PASS, pass_receipt.operation_id, record.id, 1, 40),
        fact,
        pass_receipt,
    )
    assert state.insert_evidence_once(partial) == partial
    assert state.insert_evidence_once(passed) == passed
    assert state.insert_evidence_once(passed) == passed
    state.close()

    restarted = SQLiteState(database)
    persisted = restarted.list_evidence(record.id, 1, "python", 20)
    assert persisted == (partial, passed)
    assert restarted.list_evidence(record.id, 2, "python", 20) == ()
    summary = summarize_mastery(
        fact,
        persisted,
        AdvancementThresholds(1, 2, 2, 2, 2),
        False,
        NOW + timedelta(hours=1),
    )
    assert summary.state is LearnerState.RECOGNIZED
    assert summary.supporting_evidence_ids == (passed.id,)
    with pytest.raises(DomainValidationError, match="limit"):
        restarted.list_evidence(record.id, None, None, 21)
    with pytest.raises(ReceiptConflictError):
        restarted.insert_evidence_once(dataclasses.replace(passed, criterion="different"))
    restarted.close()


def test_controls_progress_exclusions_and_deferred_state_are_durable_and_idempotent(
    tmp_path: Path,
) -> None:
    database = tmp_path / "state.sqlite3"
    state = SQLiteState(database)
    first_receipt = _authorize_receipt(
        state, PendingOperationKind.CONTROL_CHANGE, "controls-1", (), "default controls", 1
    )
    defaults = default_daily_settings("UTC", 1)
    assert state.apply_control_change(0, defaults, first_receipt.operation_id) == defaults
    assert state.apply_control_change(0, defaults, first_receipt.operation_id) == defaults

    second_receipt = _authorize_receipt(
        state,
        PendingOperationKind.CONTROL_CHANGE,
        "controls-2",
        (),
        "adjust thresholds",
        10,
    )
    adjusted = dataclasses.replace(
        defaults,
        advancement_thresholds=AdvancementThresholds(1, 2, 3, 4, 5),
        version=2,
    )
    assert state.apply_control_change(1, adjusted, second_receipt.operation_id) == adjusted
    stale_receipt = _authorize_receipt(
        state, PendingOperationKind.CONTROL_CHANGE, "controls-stale", (), "stale", 20
    )
    with pytest.raises(StaleVersionError):
        state.apply_control_change(
            1,
            dataclasses.replace(adjusted, reflection_target=2, version=2),
            stale_receipt.operation_id,
        )

    first = state.record_reflection_once("2026-09-14", "shared-reflection")
    duplicate = state.record_reflection_once("2026-09-14", "shared-reflection")
    assert first == duplicate
    assert duplicate.reflection_count == 1
    effort = state.record_effort_once("2026-09-14", "shared-effort", Decimal("2.0"))
    assert state.record_effort_once("2026-09-14", "shared-effort", Decimal("2.0")) == effort
    assert effort.effort_units == Decimal("2.0")

    exclusion_receipt = _authorize_receipt(
        state, PendingOperationKind.CONTROL_CHANGE, "exclusion-1", (), "exclude source", 30
    )
    exclusion = ScopeExclusion(
        "excluded-source",
        ExclusionKind.SOURCE,
        "source-private",
        NOW,
        exclusion_receipt.operation_id,
    )
    assert (
        state.replace_or_remove_exclusion(
            adjusted.version,
            exclusion.id,
            exclusion,
            exclusion_receipt.operation_id,
        )
        == exclusion
    )
    assert state.list_exclusions(1) == (exclusion,)
    remove_exclusion_receipt = _authorize_receipt(
        state,
        PendingOperationKind.CONTROL_CHANGE,
        "exclusion-remove",
        (),
        "remove exclusion",
        35,
    )
    assert (
        state.replace_or_remove_exclusion(
            3,
            exclusion.id,
            None,
            remove_exclusion_receipt.operation_id,
        )
        is None
    )
    assert state.list_exclusions(1) == ()

    store = backend(tmp_path / "backend", FakeBasicMemoryCli())
    record = store.create_approved(
        approved("deferred approved object", None, ("procedure",), ("domain",), ("event:defer",)),
        "deferred-knowledge",
    )
    deferred_receipt = _authorize_receipt(
        state,
        PendingOperationKind.CONTROL_CHANGE,
        "deferred-1",
        ((record.id, record.version),),
        "defer approved object",
        40,
    )
    activity = DeferredActivity(
        "deferred-activity",
        (ApprovedKnowledgeRef(record.id, record.version),),
        "explain_boundary",
        NOW,
        DeferredStatus.PENDING,
        deferred_receipt.operation_id,
    )
    assert state.insert_deferred_once(activity) == activity
    assert state.insert_deferred_once(activity) == activity
    state.close()

    restarted = SQLiteState(database)
    persisted_settings = restarted.read_control_state()
    assert persisted_settings is not None
    assert persisted_settings.advancement_thresholds == adjusted.advancement_thresholds
    assert persisted_settings.version == 4
    assert restarted.read_period_progress("2026-09-14") == effort
    assert restarted.list_exclusions(1) == ()
    assert restarted.list_deferred(DeferredStatus.PENDING, 1) == (activity,)
    removal_receipt = _authorize_receipt(
        restarted,
        PendingOperationKind.CONTROL_CHANGE,
        "deferred-remove",
        ((record.id, record.version),),
        "remove deferred object",
        50,
    )
    removed = remove_deferred(activity, removal_receipt.operation_id)
    assert restarted.remove_deferred(4, removed) == removed
    current = restarted.read_control_state()
    assert current is not None
    assert current.version == 5
    with pytest.raises(StaleVersionError):
        restarted.remove_deferred(4, removed)
    assert restarted.list_deferred(DeferredStatus.PENDING, 1) == ()
    assert restarted.list_deferred(DeferredStatus.REMOVED, 1) == (removed,)
    with pytest.raises(DomainValidationError, match="limit"):
        restarted.list_deferred(None, 0)
    columns = {
        str(row[1])
        for row in sqlite3.connect(database).execute("PRAGMA table_info(deferred_activities)")
    }
    assert "content" not in columns
    with pytest.raises(sqlite3.ProgrammingError):
        restarted.close()
        restarted.list_deferred(None, 1)


def test_progress_transaction_failure_rolls_back_without_partial_counter(tmp_path: Path) -> None:
    database = tmp_path / "state.sqlite3"
    state = SQLiteState(database)
    external = sqlite3.connect(database)
    external.execute(
        """
        CREATE TRIGGER reject_progress BEFORE INSERT ON progress_events
        BEGIN SELECT RAISE(ABORT, 'injected progress failure'); END
        """
    )
    external.commit()
    external.close()

    with pytest.raises(sqlite3.IntegrityError, match="injected progress failure"):
        state.record_reflection_once("2026-09-14", "event-fails")
    assert state.read_period_progress("2026-09-14").reflection_count == 0
    state.close()


def test_existing_c002_receipt_database_migrates_without_data_loss(tmp_path: Path) -> None:
    database = tmp_path / "legacy-state.sqlite3"
    legacy = sqlite3.connect(database)
    legacy.execute(
        """
        CREATE TABLE approval_receipts (
            operation_id TEXT PRIMARY KEY NOT NULL,
            proposal_id TEXT NOT NULL,
            operation_kind TEXT NOT NULL,
            object_refs_json TEXT NOT NULL,
            content_digest TEXT NOT NULL,
            user_event_ref TEXT NOT NULL,
            adapter_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    legacy.execute(
        "INSERT INTO approval_receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "legacy-operation",
            "legacy-proposal",
            PendingOperationKind.CREATE.value,
            '[["knowledge-legacy",1]]',
            "a" * 64,
            "legacy-user-event",
            "codex",
            NOW.isoformat(),
        ),
    )
    legacy.commit()
    legacy.close()

    migrated = SQLiteState(database)
    receipt = migrated.get_receipt("legacy-operation")
    assert receipt is not None
    assert receipt.object_ids_versions == (("knowledge-legacy", 1),)
    assert "learner_evidence" in migrated.table_names()
    migrated.close()
