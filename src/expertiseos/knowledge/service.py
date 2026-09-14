#!/usr/bin/env python3
# Purpose: Coordinate exact approved knowledge mutations through the narrow backend contract.

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import datetime
from typing import Protocol

from expertiseos.approval.gate import (
    ApprovalGate,
    DecisionGrantStore,
    canonical_approval_digest,
    child_operation_id,
)
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.domain.errors import (
    ApprovalRejectedError,
    ReadBackMismatchError,
    StaleVersionError,
)
from expertiseos.domain.models import (
    ApprovalReceipt,
    CandidateState,
    CommitResult,
    CommitStatus,
    CreateOperation,
    DecisionGrant,
    GroupedOperation,
    MutationEffect,
    PendingOperation,
    PendingOperationKind,
    RelationshipOperation,
    RelationType,
    RetireOperation,
    RevisionOperation,
)
from expertiseos.hosts.contract import DecisionObservation
from expertiseos.knowledge.backend import (
    ApprovedKnowledgeInput,
    KnowledgeBackend,
    KnowledgeRecord,
    KnowledgeStatus,
    RelationshipInput,
    VersionConflictError,
)


class ApprovalReceiptStore(Protocol):
    def record_receipt(self, receipt: ApprovalReceipt) -> ApprovalReceipt: ...

    def get_receipt(self, operation_id: str) -> ApprovalReceipt | None: ...


class KnowledgeService:
    """Expose proposal and approved-read operations without a mutation bypass."""

    def __init__(
        self,
        backend: KnowledgeBackend,
        candidates: CandidateStore,
        grants: DecisionGrantStore,
        gate: ApprovalGate,
        receipts: ApprovalReceiptStore,
        clock: Callable[[], datetime],
    ) -> None:
        self._backend = backend
        self._candidates = candidates
        self._grants = grants
        self._gate = gate
        self._receipts = receipts
        self._clock = clock
        self._attempted: set[str] = set()

    def propose_create(
        self,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        value: ApprovedKnowledgeInput,
        created_at: datetime,
    ) -> PendingOperation:
        return self._propose(
            proposal_id,
            operation_id,
            session_id,
            adapter_id,
            PendingOperationKind.CREATE,
            CreateOperation(value),
            (),
            created_at,
        )

    def propose_direct_create(
        self,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        value: ApprovedKnowledgeInput,
        observation: DecisionObservation,
        grant_id: str,
        created_at: datetime,
    ) -> tuple[PendingOperation, DecisionGrant]:
        self.propose_create(proposal_id, operation_id, session_id, adapter_id, value, created_at)
        self.present(proposal_id)
        grant = self.register_decision(proposal_id, grant_id, observation, created_at)
        current = self._candidates.get(proposal_id)
        assert current is not None
        return current, grant

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
    ) -> PendingOperation:
        return self._propose(
            proposal_id,
            operation_id,
            session_id,
            adapter_id,
            PendingOperationKind.REVISE,
            RevisionOperation(knowledge_id, expected_version, value),
            ((knowledge_id, expected_version),),
            created_at,
        )

    def propose_relation_change(
        self,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        relationships: tuple[RelationshipInput, ...],
        expected_versions: Mapping[str, int],
        created_at: datetime,
    ) -> PendingOperation:
        normalized = tuple(sorted(expected_versions.items()))
        for relationship in relationships:
            try:
                RelationType(relationship.type)
            except ValueError as error:
                raise ValueError("unsupported relationship type") from error
            if expected_versions.get(relationship.source_id) != relationship.source_version:
                raise ValueError("relationship source version is not bound")
            if expected_versions.get(relationship.target_id) != relationship.target_version:
                raise ValueError("relationship target version is not bound")
        return self._propose(
            proposal_id,
            operation_id,
            session_id,
            adapter_id,
            PendingOperationKind.RELATION,
            RelationshipOperation(relationships, normalized),
            normalized,
            created_at,
        )

    def propose_retirement(
        self,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        knowledge_id: str,
        expected_version: int,
        created_at: datetime,
    ) -> PendingOperation:
        return self._propose(
            proposal_id,
            operation_id,
            session_id,
            adapter_id,
            PendingOperationKind.RETIRE,
            RetireOperation(knowledge_id, expected_version),
            ((knowledge_id, expected_version),),
            created_at,
        )

    def propose_grouped(
        self,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        kind: PendingOperationKind,
        effects: tuple[MutationEffect, ...],
        expected_versions: Mapping[str, int],
        created_at: datetime,
    ) -> PendingOperation:
        if kind is not PendingOperationKind.CONFLICT_RESOLUTION:
            raise ValueError("grouped operation kind must be conflict_resolution")
        normalized = tuple(sorted(expected_versions.items()))
        return self._propose(
            proposal_id,
            operation_id,
            session_id,
            adapter_id,
            kind,
            GroupedOperation(effects),
            normalized,
            created_at,
        )

    def _propose(
        self,
        proposal_id: str,
        operation_id: str,
        session_id: str,
        adapter_id: str,
        kind: PendingOperationKind,
        payload: MutationEffect | GroupedOperation,
        expected_versions: tuple[tuple[str, int], ...],
        created_at: datetime,
    ) -> PendingOperation:
        self._validate_payload_kind(kind, payload)
        digest = canonical_approval_digest(kind, payload, expected_versions)
        proposal = PendingOperation(
            proposal_id,
            operation_id,
            session_id,
            adapter_id,
            kind,
            CandidateState.DETECTED,
            payload,
            digest,
            expected_versions,
            created_at,
        )
        return self._candidates.create_detected(proposal)

    def present(self, proposal_id: str) -> PendingOperation:
        self._candidates.mark_awaiting_checkpoint(proposal_id)
        return self._candidates.mark_awaiting_decision(proposal_id)

    def revise_displayed_proposal(
        self, proposal_id: str, payload: MutationEffect | GroupedOperation
    ) -> PendingOperation:
        proposal = self._candidates.get(proposal_id)
        if proposal is None:
            raise ApprovalRejectedError("proposal not found")
        if proposal.state is not CandidateState.AWAITING_DECISION:
            raise ApprovalRejectedError("proposal is not awaiting a decision")
        self._validate_payload_kind(proposal.kind, payload)
        self._grants.expire_proposal(proposal_id)
        updated = replace(
            proposal,
            payload=payload,
            content_digest=canonical_approval_digest(
                proposal.kind, payload, proposal.expected_versions
            ),
        )
        return self._candidates.replace_awaiting_decision(updated)

    @staticmethod
    def _validate_payload_kind(
        kind: PendingOperationKind, payload: MutationEffect | GroupedOperation
    ) -> None:
        expected_type: type[object]
        if kind is PendingOperationKind.CREATE:
            expected_type = CreateOperation
        elif kind is PendingOperationKind.REVISE:
            expected_type = RevisionOperation
        elif kind is PendingOperationKind.RELATION:
            expected_type = RelationshipOperation
        elif kind is PendingOperationKind.RETIRE:
            expected_type = RetireOperation
        elif kind is PendingOperationKind.CONFLICT_RESOLUTION:
            expected_type = GroupedOperation
        else:
            raise ValueError("operation kind is not implemented by consent core")
        if not isinstance(payload, expected_type):
            raise ValueError("operation payload does not match operation kind")

    def register_decision(
        self,
        proposal_id: str,
        grant_id: str,
        observation: DecisionObservation,
        created_at: datetime,
    ) -> DecisionGrant:
        proposal = self._candidates.get(proposal_id)
        if proposal is None:
            raise ApprovalRejectedError("proposal not found")
        return self._grants.register(proposal, observation, grant_id, created_at)

    def decline(self, proposal_id: str, fingerprint: str | None) -> PendingOperation:
        proposal = self._candidates.decline(proposal_id, fingerprint)
        self._grants.expire_proposal(proposal_id)
        return proposal

    def expire_session(self, session_id: str) -> tuple[str, ...]:
        expired = self._candidates.expire_session(session_id)
        self._grants.expire_session(session_id)
        return expired

    def expire_unrelated_decisions(
        self, session_id: str, active_proposal_id: str | None
    ) -> tuple[str, ...]:
        expired = self._candidates.expire_unrelated_decisions(session_id, active_proposal_id)
        for proposal_id in expired:
            self._grants.expire_proposal(proposal_id)
        return expired

    def commit(self, proposal_id: str, grant_id: str, operation_id: str) -> CommitResult:
        proposal = self._candidates.get(proposal_id)
        grant = self._grants.get(grant_id)
        if proposal is None or grant is None:
            return CommitResult(CommitStatus.REJECTED, (), None, "approval_rejected")
        try:
            existing = self._receipts.get_receipt(operation_id)
        except Exception as error:
            return CommitResult(CommitStatus.FAILED, (), None, error.__class__.__name__)
        if existing is not None:
            return self._finish_existing(proposal, grant_id, operation_id, existing)
        try:
            current_versions = self._backend.get_current_versions(
                tuple(key for key, _ in proposal.expected_versions)
            )
            expected_versions = dict(proposal.expected_versions)
            versions_stale = dict(current_versions) != expected_versions
            allow_replay = operation_id in self._attempted and versions_stale
            self._gate.validate(proposal, grant, operation_id, current_versions, allow_replay)
        except StaleVersionError as error:
            return CommitResult(CommitStatus.CONFLICT, (), None, error.__class__.__name__)
        except ApprovalRejectedError as error:
            return CommitResult(CommitStatus.REJECTED, (), None, error.__class__.__name__)
        except Exception as error:
            return CommitResult(CommitStatus.FAILED, (), None, error.__class__.__name__)

        self._attempted.add(operation_id)
        try:
            records = self._execute(proposal.payload, operation_id)
            self._verify_approved_effect(proposal.payload, records)
            self._verify_read_back(records)
        except VersionConflictError as error:
            return CommitResult(CommitStatus.CONFLICT, (), None, error.__class__.__name__)
        except Exception as error:
            return CommitResult(CommitStatus.FAILED, (), None, error.__class__.__name__)

        receipt = ApprovalReceipt(
            operation_id,
            proposal.proposal_id,
            proposal.kind,
            tuple(sorted({record.id: record.version for record in records}.items())),
            proposal.content_digest,
            grant.user_event_ref,
            proposal.adapter_id,
            self._clock(),
        )
        try:
            stored = self._receipts.record_receipt(receipt)
        except Exception as error:
            return CommitResult(CommitStatus.INCOMPLETE, records, None, error.__class__.__name__)
        try:
            self._grants.consume(grant_id, self._clock())
            self._grants.expire_proposal(proposal_id)
            self._candidates.mark_approved(proposal_id)
        except Exception as error:
            return CommitResult(CommitStatus.INCOMPLETE, records, stored, error.__class__.__name__)
        return CommitResult(CommitStatus.COMMITTED, records, stored, None)

    def _finish_existing(
        self,
        proposal: PendingOperation,
        grant_id: str,
        operation_id: str,
        receipt: ApprovalReceipt,
    ) -> CommitResult:
        grant = self._grants.get(grant_id)
        if (
            grant is None
            or proposal.operation_id != operation_id
            or receipt.proposal_id != proposal.proposal_id
            or receipt.content_digest != proposal.content_digest
            or receipt.operation_kind is not proposal.kind
            or receipt.adapter_id != proposal.adapter_id
            or grant.proposal_id != proposal.proposal_id
            or grant.session_id != proposal.session_id
            or grant.adapter_id != proposal.adapter_id
            or grant.content_digest != proposal.content_digest
            or grant.expected_versions != proposal.expected_versions
            or grant.user_event_ref != receipt.user_event_ref
            or grant.action.value not in {"save", "confirm_change"}
            or canonical_approval_digest(
                proposal.kind, proposal.payload, proposal.expected_versions
            )
            != proposal.content_digest
        ):
            return CommitResult(CommitStatus.REJECTED, (), None, "approval_rejected")
        records: list[KnowledgeRecord] = []
        for knowledge_id, version in receipt.object_ids_versions:
            record = self._backend.get(knowledge_id, version, include_retired=True)
            if record is None:
                return CommitResult(CommitStatus.FAILED, (), None, "ReadBackMismatchError")
            records.append(record)
        if grant.consumed_at is None:
            self._grants.consume(grant_id, self._clock())
            self._grants.expire_proposal(proposal.proposal_id)
        if proposal.state is CandidateState.AWAITING_DECISION:
            self._candidates.mark_approved(proposal.proposal_id)
        return CommitResult(CommitStatus.COMMITTED, tuple(records), receipt, None)

    def _execute(
        self, payload: MutationEffect | GroupedOperation, operation_id: str
    ) -> tuple[KnowledgeRecord, ...]:
        if isinstance(payload, GroupedOperation):
            records: list[KnowledgeRecord] = []
            for index, effect in enumerate(payload.effects):
                child_id = child_operation_id(operation_id, index, type(effect).__name__)
                child_records = self._execute(effect, child_id)
                self._verify_approved_effect(effect, child_records)
                records.extend(child_records)
            return tuple(records)
        if isinstance(payload, CreateOperation):
            return (self._backend.create_approved(payload.value, operation_id),)
        if isinstance(payload, RevisionOperation):
            return (
                self._backend.update_approved(
                    payload.knowledge_id,
                    payload.expected_version,
                    payload.value,
                    operation_id,
                ),
            )
        if isinstance(payload, RelationshipOperation):
            return self._backend.set_relationships(
                payload.relationships, dict(payload.expected_versions), operation_id
            )
        if isinstance(payload, RetireOperation):
            return (
                self._backend.retire(payload.knowledge_id, payload.expected_version, operation_id),
            )
        raise TypeError("unsupported approved operation")

    def _verify_approved_effect(
        self,
        payload: MutationEffect | GroupedOperation,
        records: tuple[KnowledgeRecord, ...],
    ) -> None:
        if isinstance(payload, GroupedOperation):
            return
        if isinstance(payload, CreateOperation | RevisionOperation):
            if len(records) != 1 or not self._record_matches_input(records[0], payload.value):
                raise ReadBackMismatchError("mutation result differs from approved content")
            if isinstance(payload, RevisionOperation) and (
                records[0].id != payload.knowledge_id
                or records[0].version != payload.expected_version + 1
            ):
                raise ReadBackMismatchError("revision identity or version is incorrect")
            return
        if isinstance(payload, RetireOperation):
            if (
                len(records) != 1
                or records[0].id != payload.knowledge_id
                or records[0].version != payload.expected_version + 1
                or records[0].status is not KnowledgeStatus.RETIRED
            ):
                raise ReadBackMismatchError("retirement result is incorrect")
            return
        if isinstance(payload, RelationshipOperation):
            expected_sources = {item.source_id for item in payload.relationships}
            actual_sources = {record.id for record in records}
            if actual_sources != expected_sources:
                raise ReadBackMismatchError("relationship result sources are incorrect")
            for record in records:
                selected = tuple(
                    item for item in payload.relationships if item.source_id == record.id
                )
                if record.relationships != selected:
                    raise ReadBackMismatchError("relationship result differs from approval")
            return
        raise ReadBackMismatchError("unsupported approved effect")

    @staticmethod
    def _record_matches_input(record: KnowledgeRecord, value: ApprovedKnowledgeInput) -> bool:
        return (
            record.content == value.content
            and record.content_digest == value.content_digest
            and record.categories == value.categories
            and record.subjects == value.subjects
            and record.applicability_scope == value.applicability_scope
            and record.evidential_status == value.evidential_status
            and record.source_refs == value.source_refs
            and record.contribution_origin == value.contribution_origin
            and record.status is KnowledgeStatus.ACTIVE
        )

    def _verify_read_back(self, records: tuple[KnowledgeRecord, ...]) -> None:
        expected_versions = {record.id: record.version for record in records}
        current = self._backend.get_current_versions(tuple(sorted(expected_versions)))
        if dict(current) != expected_versions:
            raise ReadBackMismatchError("current versions do not match mutation result")
        for record in records:
            stored = self._backend.get(record.id, record.version, include_retired=True)
            if stored != record:
                raise ReadBackMismatchError("versioned read-back does not match mutation result")

    def get(
        self,
        knowledge_id: str,
        version: int | None,
        include_retired: bool,
    ) -> KnowledgeRecord | None:
        return self._backend.get(knowledge_id, version, include_retired)
