#!/usr/bin/env python3
# Purpose: Compose promoted expertiseOS services behind one guarded host-neutral facade.

"""Host-neutral expertiseOS product composition."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from expertiseos.domain.models import CommitResult, CommitStatus
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
from expertiseos.learning.controls import DeferredActivity, resolve_controls
from expertiseos.learning.evidence import (
    AdvancementThresholds,
    ApprovedObjectFact,
    summarize_mastery,
)
from expertiseos.learning.evidence import inspect_learning_state as build_learning_inspection
from expertiseos.ownership import (
    ApprovedSnapshotSource,
    ExportRequestBinding,
    ExportScope,
    OwnershipStatus,
    RestorePlan,
    RestoreRequestBinding,
    RestoreTarget,
    SelectionAuthority,
    export_approved,
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

    def propose_learning_evidence(self, operation_id: str, request: object) -> ToolResult:
        del operation_id, request
        return self._result(
            ToolStatus.UNAVAILABLE,
            None,
            "guarded_learning_producer_unavailable",
            "Learning evidence writes unavailable",
            (),
        )

    def decline_proposal(self, proposal_id: str, fingerprint: str | None) -> ToolResult:
        try:
            proposal = self._knowledge.decline(proposal_id, fingerprint)
        except Exception as error:
            return self._result(
                ToolStatus.REJECTED, None, type(error).__name__, "Decline rejected", ()
            )
        return self._result(ToolStatus.OK, proposal, None, "Declined", ())

    def commit_proposal(self, proposal_id: str, grant_id: str, operation_id: str) -> ToolResult:
        result = self._knowledge.commit(proposal_id, grant_id, operation_id)
        return self._commit_tool_result(result)

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

    def propose_control_change(self, operation_id: str, request: object) -> ToolResult:
        del operation_id, request
        return self._result(
            ToolStatus.UNAVAILABLE,
            None,
            "guarded_control_producer_unavailable",
            "Control writes unavailable",
            (),
        )

    def propose_retire_or_delete(self, operation_id: str, request: object) -> ToolResult:
        del operation_id, request
        return self._result(
            ToolStatus.UNAVAILABLE,
            None,
            "guarded_delete_producer_unavailable",
            "Delete writes unavailable",
            (),
        )

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
        self, operation_id: str, expected_version: int, activity: DeferredActivity
    ) -> ToolResult:
        if operation_id != activity.approval_receipt_id:
            return self._result(
                ToolStatus.REJECTED,
                None,
                "operation_id_mismatch",
                "Removal rejected",
                (),
            )
        try:
            removed = self._state.remove_deferred(expected_version, activity)
        except Exception as error:
            return self._result(
                ToolStatus.REJECTED, None, type(error).__name__, "Removal rejected", ()
            )
        return self._result(ToolStatus.COMMITTED, removed, None, "Removed", ())

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
