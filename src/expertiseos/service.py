#!/usr/bin/env python3
# Purpose: Compose promoted expertiseOS services behind one guarded host-neutral facade.

"""Host-neutral expertiseOS product composition."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from expertiseos.domain.errors import (
    ApprovalRejectedError,
    ReceiptConflictError,
    StaleVersionError,
)
from expertiseos.domain.models import (
    ApprovalReceipt,
    AuthorizedOperation,
    CommitResult,
    CommitStatus,
    ControlChangeOperation,
    DeleteOperation,
    LearningEvidenceOperation,
)
from expertiseos.hosts.contract import HostAdapter, HostCapability
from expertiseos.knowledge.backend import (
    ApprovedKnowledgeInput,
    IndexState,
    KnowledgeBackend,
    RelationshipInput,
    SearchQuery,
    StoreState,
)
from expertiseos.knowledge.service import KnowledgeService
from expertiseos.learning.controls import (
    ControlSettings,
    DeferredActivity,
    DeferredStatus,
    resolve_controls,
)
from expertiseos.learning.evidence import (
    AdvancementThresholds,
    ApprovedObjectFact,
    LearnerEvidence,
    summarize_mastery,
)
from expertiseos.learning.evidence import inspect_learning_state as build_learning_inspection
from expertiseos.ownership import (
    ApprovedSnapshotSource,
    DeletionScope,
    ExportRequestBinding,
    ExportScope,
    OwnershipStatus,
    RestorePlan,
    RestoreRequestBinding,
    RestoreTarget,
    SelectionAuthority,
    SQLiteLearningDeletionTarget,
    execute_delete,
    export_approved,
    plan_delete,
    restore_validated,
)
from expertiseos.state.sqlite import SQLiteState


class ToolStatus(StrEnum):
    OK = "ok"
    COMMITTED = "committed"
    REJECTED = "rejected"
    CONFLICT = "conflict"
    FAILED = "failed"
    INCOMPLETE = "incomplete"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ToolResult:
    status: ToolStatus
    data: object | None
    error_code: str | None
    message: str
    capabilities: tuple[HostCapability, ...]

    @property
    def render_saved(self) -> bool:
        return self.status is ToolStatus.COMMITTED and self.message == "Saved"


class ExpertiseOSService:
    """Compose promoted services without owning product state or authorization policy."""

    def __init__(
        self,
        knowledge: KnowledgeService,
        backend: KnowledgeBackend,
        state: SQLiteState,
        adapters: tuple[HostAdapter, ...],
    ) -> None:
        adapter_ids = tuple(adapter.adapter_id for adapter in adapters)
        if len(adapter_ids) != len(set(adapter_ids)):
            raise ValueError("adapter ids must be unique")
        self._knowledge = knowledge
        self._backend = backend
        self._state = state
        self._adapters = {adapter.adapter_id: adapter for adapter in adapters}

    @staticmethod
    def _result(
        status: ToolStatus,
        data: object | None,
        error_code: str | None,
        message: str,
        capabilities: tuple[HostCapability, ...],
    ) -> ToolResult:
        return ToolResult(status, data, error_code, message, capabilities)

    def search_knowledge(self, query: SearchQuery) -> ToolResult:
        try:
            response = self._knowledge.search(query)
        except Exception as error:
            return self._result(
                ToolStatus.UNAVAILABLE, None, type(error).__name__, "Search unavailable", ()
            )
        if response.canonical_store is StoreState.UNAVAILABLE:
            status = ToolStatus.UNAVAILABLE
        elif response.degraded:
            status = ToolStatus.DEGRADED
        else:
            status = ToolStatus.OK
        return self._result(status, response, None, "Search complete", ())

    def get_knowledge(
        self, knowledge_id: str, version: int | None, include_retired: bool
    ) -> ToolResult:
        try:
            record = self._knowledge.get(knowledge_id, version, include_retired)
        except Exception as error:
            return self._result(
                ToolStatus.UNAVAILABLE, None, type(error).__name__, "Read unavailable", ()
            )
        if record is None:
            return self._result(ToolStatus.REJECTED, None, "not_found", "Not found", ())
        return self._result(ToolStatus.OK, record, None, "Read complete", ())

    def inspect_learning_state(
        self,
        fact: ApprovedObjectFact,
        thresholds: AdvancementThresholds,
        autonomous_agreement: bool,
        inspected_at: datetime,
    ) -> ToolResult:
        try:
            evidence = self._state.list_evidence(
                fact.knowledge_id, fact.knowledge_version, fact.requested_scope, 20
            )
            summary = summarize_mastery(
                fact, evidence, thresholds, autonomous_agreement, inspected_at
            )
            inspection = build_learning_inspection(summary, evidence, 20)
        except Exception as error:
            return self._result(
                ToolStatus.FAILED, None, type(error).__name__, "Learning state unavailable", ()
            )
        return self._result(ToolStatus.OK, inspection, None, "Learning state ready", ())

    def inspect_controls(self, period_key: str, inspected_at: datetime) -> ToolResult:
        try:
            settings = self._state.read_control_state()
            if settings is None:
                return self._result(
                    ToolStatus.UNAVAILABLE,
                    None,
                    "controls_not_configured",
                    "Controls unavailable",
                    (),
                )
            progress = self._state.read_period_progress(period_key)
            resolution = resolve_controls(settings, progress, inspected_at)
        except Exception as error:
            return self._result(
                ToolStatus.FAILED, None, type(error).__name__, "Controls unavailable", ()
            )
        return self._result(ToolStatus.OK, resolution, None, "Controls ready", ())

    def inspect_capabilities(self, adapter_id: str) -> ToolResult:
        adapter = self._adapters.get(adapter_id)
        if adapter is None:
            return self._result(ToolStatus.REJECTED, None, "unknown_adapter", "Unknown adapter", ())
        capabilities = adapter.capabilities()
        return self._result(ToolStatus.OK, capabilities, None, "Capabilities ready", capabilities)

    def health(self) -> ToolResult:
        try:
            health = self._backend.health()
        except Exception as error:
            return self._result(
                ToolStatus.UNAVAILABLE, None, type(error).__name__, "Service unavailable", ()
            )
        if health.canonical_store is StoreState.UNAVAILABLE:
            status = ToolStatus.UNAVAILABLE
        elif health.canonical_store is not StoreState.READY or health.index is not IndexState.READY:
            status = ToolStatus.DEGRADED
        else:
            status = ToolStatus.OK
        return self._result(status, health, None, "Health ready", ())

    def propose_create_knowledge(
        self,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        value: ApprovedKnowledgeInput,
        created_at: datetime,
    ) -> ToolResult:
        try:
            proposal = self._knowledge.propose_create(
                proposal_id, operation_id, session_id, adapter_id, value, created_at
            )
            presented = self._knowledge.present(proposal.proposal_id)
        except Exception as error:
            return self._result(
                ToolStatus.REJECTED, None, type(error).__name__, "Proposal rejected", ()
            )
        return self._result(ToolStatus.OK, presented, None, "Proposal ready", ())

    def propose_revision(
        self,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        knowledge_id: str,
        expected_version: int,
        value: ApprovedKnowledgeInput,
        created_at: datetime,
    ) -> ToolResult:
        try:
            proposal = self._knowledge.propose_revision(
                proposal_id,
                operation_id,
                session_id,
                adapter_id,
                knowledge_id,
                expected_version,
                value,
                created_at,
            )
            presented = self._knowledge.present(proposal.proposal_id)
        except Exception as error:
            return self._result(
                ToolStatus.REJECTED, None, type(error).__name__, "Proposal rejected", ()
            )
        return self._result(ToolStatus.OK, presented, None, "Proposal ready", ())

    def propose_relation_change(
        self,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        relationships: tuple[RelationshipInput, ...],
        expected_versions: Mapping[str, int],
        created_at: datetime,
    ) -> ToolResult:
        try:
            proposal = self._knowledge.propose_relation_change(
                proposal_id,
                operation_id,
                session_id,
                adapter_id,
                relationships,
                expected_versions,
                created_at,
            )
            presented = self._knowledge.present(proposal.proposal_id)
        except Exception as error:
            return self._result(
                ToolStatus.REJECTED, None, type(error).__name__, "Proposal rejected", ()
            )
        return self._result(ToolStatus.OK, presented, None, "Proposal ready", ())

    def propose_learning_evidence(
        self,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        evidence: LearnerEvidence,
        expected_versions: Mapping[str, int],
        created_at: datetime,
    ) -> ToolResult:
        return self._propose_delegated(
            self._knowledge.propose_learning_evidence,
            proposal_id,
            operation_id,
            session_id,
            adapter_id,
            evidence,
            expected_versions,
            created_at,
        )

    def decline_proposal(self, proposal_id: str, fingerprint: str | None) -> ToolResult:
        try:
            proposal = self._knowledge.decline(proposal_id, fingerprint)
        except Exception as error:
            return self._result(
                ToolStatus.REJECTED, None, type(error).__name__, "Decline rejected", ()
            )
        return self._result(ToolStatus.OK, proposal, None, "Declined", ())

    def commit_proposal(
        self,
        proposal_id: str,
        grant_id: str,
        operation_id: str,
        expected_versions: Mapping[str, int],
    ) -> ToolResult:
        current_versions = self._resolve_current_versions(tuple(expected_versions))
        try:
            authorization = self._knowledge.prepare_delegated_commit(
                proposal_id,
                grant_id,
                operation_id,
                current_versions,
            )
        except ApprovalRejectedError:
            result = self._knowledge.commit(proposal_id, grant_id, operation_id)
            return self._commit_tool_result(result)
        except StaleVersionError as error:
            return self._result(ToolStatus.CONFLICT, None, type(error).__name__, "Conflict", ())
        except ReceiptConflictError as error:
            return self._result(ToolStatus.CONFLICT, None, type(error).__name__, "Conflict", ())
        except Exception as error:
            return self._result(ToolStatus.REJECTED, None, type(error).__name__, "Rejected", ())
        return self._execute_delegated(authorization)

    def _commit_tool_result(self, result: CommitResult) -> ToolResult:
        statuses = {
            CommitStatus.COMMITTED: ToolStatus.COMMITTED,
            CommitStatus.REJECTED: ToolStatus.REJECTED,
            CommitStatus.CONFLICT: ToolStatus.CONFLICT,
            CommitStatus.FAILED: ToolStatus.FAILED,
            CommitStatus.INCOMPLETE: ToolStatus.INCOMPLETE,
        }
        status = statuses[result.status]
        message = "Saved" if status is ToolStatus.COMMITTED else status.value.capitalize()
        return self._result(status, result, result.error_code, message, ())

    def propose_control_change(
        self,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        change: ControlSettings | DeferredActivity,
        expected_versions: Mapping[str, int],
        created_at: datetime,
    ) -> ToolResult:
        return self._propose_delegated(
            self._knowledge.propose_control_change,
            proposal_id,
            operation_id,
            session_id,
            adapter_id,
            change,
            expected_versions,
            created_at,
        )

    def propose_retire_or_delete(
        self,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        scope: DeletionScope,
        expected_versions: Mapping[str, int],
        created_at: datetime,
    ) -> ToolResult:
        return self._propose_delegated(
            self._knowledge.propose_delete,
            proposal_id,
            operation_id,
            session_id,
            adapter_id,
            scope,
            expected_versions,
            created_at,
        )

    def _propose_delegated(
        self,
        proposer: object,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        value: object,
        expected_versions: Mapping[str, int],
        created_at: datetime,
    ) -> ToolResult:
        if not callable(proposer):
            raise TypeError("delegated proposer must be callable")
        try:
            proposal = proposer(
                proposal_id,
                operation_id,
                session_id,
                adapter_id,
                value,
                expected_versions,
                created_at,
            )
            presented = self._knowledge.present(proposal.proposal_id)
        except Exception as error:
            return self._result(
                ToolStatus.REJECTED, None, type(error).__name__, "Proposal rejected", ()
            )
        return self._result(ToolStatus.OK, presented, None, "Proposal ready", ())

    def _resolve_current_versions(self, keys: tuple[str, ...]) -> dict[str, int]:
        actual: dict[str, int] = {}
        knowledge_ids = tuple(sorted(key for key in keys if key != "control-state"))
        if knowledge_ids:
            actual.update(self._backend.get_current_versions(knowledge_ids))
        if "control-state" in keys:
            settings = self._state.read_control_state()
            actual["control-state"] = 0 if settings is None else settings.version
        return actual

    def _execute_delegated(self, authorization: AuthorizedOperation) -> ToolResult:
        try:
            affected = self._affected_versions(authorization)
            receipt = authorization.existing_receipt
            if receipt is None:
                receipt = ApprovalReceipt(
                    authorization.operation_id,
                    authorization.proposal_id,
                    authorization.kind,
                    affected,
                    authorization.content_digest,
                    authorization.user_event_ref,
                    authorization.adapter_id,
                    datetime.now(UTC),
                )
            elif receipt.object_ids_versions != affected:
                raise ReceiptConflictError("receipt affected versions changed")
            self._state.record_receipt(receipt)
            data = self._write_and_read_back(authorization, receipt)
            self._knowledge.complete_delegated_commit(authorization, affected)
        except StaleVersionError as error:
            return self._result(ToolStatus.CONFLICT, None, type(error).__name__, "Conflict", ())
        except ReceiptConflictError as error:
            return self._result(ToolStatus.CONFLICT, None, type(error).__name__, "Conflict", ())
        except Exception as error:
            return self._result(
                ToolStatus.INCOMPLETE,
                None,
                type(error).__name__,
                "Incomplete",
                (),
            )
        return self._result(ToolStatus.COMMITTED, data, None, "Saved", ())

    @staticmethod
    def _affected_versions(authorization: AuthorizedOperation) -> tuple[tuple[str, int], ...]:
        payload = authorization.payload
        if isinstance(payload, LearningEvidenceOperation):
            evidence = payload.value
            if not isinstance(evidence, LearnerEvidence):
                raise TypeError("learning evidence payload is invalid")
            return ((evidence.knowledge_id, evidence.knowledge_version),)
        if isinstance(payload, ControlChangeOperation):
            value = payload.value
            if isinstance(value, ControlSettings):
                return (("control-state", value.version),)
            if isinstance(value, DeferredActivity):
                refs = tuple((item.knowledge_id, item.version) for item in value.knowledge_refs)
                current = dict(authorization.expected_versions).get("control-state")
                if current is None:
                    raise ValueError("deferred removal requires control-state version")
                return tuple(sorted(refs + (("control-state", current + 1),)))
            raise TypeError("control payload is invalid")
        if isinstance(payload, DeleteOperation) and isinstance(payload.value, DeletionScope):
            return tuple(
                sorted((item.knowledge_id, item.version) for item in payload.value.object_refs)
            )
        raise TypeError("delegated payload is invalid")

    def _write_and_read_back(
        self, authorization: AuthorizedOperation, receipt: ApprovalReceipt
    ) -> object:
        payload = authorization.payload
        if isinstance(payload, LearningEvidenceOperation):
            evidence = payload.value
            if not isinstance(evidence, LearnerEvidence):
                raise TypeError("learning evidence payload is invalid")
            stored = self._state.insert_evidence_once(evidence)
            if self._state.insert_evidence_once(evidence) != stored:
                raise RuntimeError("learning evidence readback mismatch")
            return stored
        if isinstance(payload, ControlChangeOperation):
            return self._write_control_payload(authorization, payload.value)
        if isinstance(payload, DeleteOperation) and isinstance(payload.value, DeletionScope):
            plan = plan_delete(payload.value, receipt)
            result = execute_delete(
                plan,
                self._backend,
                SQLiteLearningDeletionTarget(self._state),
            )
            if result.status is not OwnershipStatus.COMMITTED:
                raise RuntimeError("delete did not complete")
            for ref in plan.object_refs:
                if self._backend.get(ref.knowledge_id, ref.version, True) is not None:
                    raise RuntimeError("deleted knowledge remains")
                if self._state.list_evidence(ref.knowledge_id, ref.version, None, 1):
                    raise RuntimeError("deleted learning evidence remains")
            return result
        raise TypeError("delegated payload is invalid")

    def _write_control_payload(self, authorization: AuthorizedOperation, value: object) -> object:
        if isinstance(value, ControlSettings):
            control_expected = value.version - 1
            stored_settings = self._state.apply_control_change(
                control_expected, value, authorization.operation_id
            )
            if self._state.read_control_state() != stored_settings:
                raise RuntimeError("control readback mismatch")
            return stored_settings
        if isinstance(value, DeferredActivity):
            deferred_expected = dict(authorization.expected_versions).get("control-state")
            if deferred_expected is None or value.status is not DeferredStatus.REMOVED:
                raise ValueError("deferred removal payload is invalid")
            stored_activity = self._state.remove_deferred(deferred_expected, value)
            readback = self._state.list_deferred(DeferredStatus.REMOVED, 20)
            if stored_activity not in readback:
                raise RuntimeError("deferred removal readback mismatch")
            settings = self._state.read_control_state()
            if settings is None or settings.version != deferred_expected + 1:
                raise RuntimeError("deferred control version readback mismatch")
            return stored_activity
        raise TypeError("control payload is invalid")

    def export_data(
        self,
        binding: ExportRequestBinding,
        scope: ExportScope,
        destination: Path,
        source: ApprovedSnapshotSource,
        authority: SelectionAuthority,
        product_version: str,
        created_at: datetime,
    ) -> ToolResult:
        result = export_approved(
            binding, scope, destination, source, authority, product_version, created_at
        )
        return self._ownership_result(result.status, result, result.error_code, "Exported")

    def restore_data(
        self,
        plan: RestorePlan,
        binding: RestoreRequestBinding,
        authority: SelectionAuthority,
        target: RestoreTarget,
    ) -> ToolResult:
        result = restore_validated(plan, binding, authority, target)
        return self._ownership_result(result.status, result, result.error_code, "Restored")

    def remove_deferred_activity(
        self,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        activity: DeferredActivity,
        expected_versions: Mapping[str, int],
        created_at: datetime,
    ) -> ToolResult:
        return self.propose_control_change(
            proposal_id,
            operation_id,
            session_id,
            adapter_id,
            activity,
            expected_versions,
            created_at,
        )

    def _ownership_result(
        self, status: OwnershipStatus, data: object, error_code: str | None, success: str
    ) -> ToolResult:
        statuses = {
            OwnershipStatus.COMMITTED: ToolStatus.COMMITTED,
            OwnershipStatus.REJECTED: ToolStatus.REJECTED,
            OwnershipStatus.CONFLICT: ToolStatus.CONFLICT,
            OwnershipStatus.INCOMPLETE: ToolStatus.INCOMPLETE,
            OwnershipStatus.REPAIR_REQUIRED: ToolStatus.INCOMPLETE,
        }
        selected = statuses[status]
        message = success if selected is ToolStatus.COMMITTED else selected.value.capitalize()
        return self._result(selected, data, error_code, message, ())
