#!/usr/bin/env python3
# Purpose: Validate approved learner evidence and derive deterministic mastery summaries.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from expertiseos.domain.errors import DomainValidationError
from expertiseos.domain.models import ApprovalReceipt, LearnerState, PendingOperationKind
from expertiseos.knowledge.backend import SearchResult

_STATE_ORDER = (
    LearnerState.NEW,
    LearnerState.RECOGNIZED,
    LearnerState.EXPLAINED,
    LearnerState.APPLIED,
    LearnerState.TRANSFERRED,
    LearnerState.AUTONOMOUS,
)
_STATE_RANK = {state: index for index, state in enumerate(_STATE_ORDER)}


def _require_text(value: str, name: str) -> None:
    if not value or not value.strip():
        raise DomainValidationError(f"{name} is required")


def _require_optional_text(value: str | None, name: str) -> None:
    if value is not None and not value.strip():
        raise DomainValidationError(f"{name} cannot be blank")


def _require_utc(value: datetime, name: str) -> None:
    offset = value.utcoffset()
    if value.tzinfo is None or offset is None or offset.total_seconds() != 0:
        raise DomainValidationError(f"{name} must be UTC")


class EvidenceOutcome(StrEnum):
    PASS = "pass"
    PARTIAL = "partial"
    FAIL = "fail"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class AssistanceLevel(StrEnum):
    INDEPENDENT = "independent"
    ASSISTED = "assisted"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AdvancementThresholds:
    recognized_passes: int
    explained_passes: int
    applied_passes: int
    transferred_passes: int
    autonomous_passes: int

    def __post_init__(self) -> None:
        values = self.as_tuple()
        if any(type(value) is not int or value < 1 for value in values):
            raise DomainValidationError("advancement thresholds must be positive integers")
        if tuple(sorted(values)) != values:
            raise DomainValidationError("advancement thresholds must be nondecreasing")
        if self.autonomous_passes < 2:
            raise DomainValidationError("autonomous threshold must be at least two")

    def as_tuple(self) -> tuple[int, int, int, int, int]:
        return (
            self.recognized_passes,
            self.explained_passes,
            self.applied_passes,
            self.transferred_passes,
            self.autonomous_passes,
        )

    def for_state(self, state: LearnerState) -> int:
        values = {
            LearnerState.RECOGNIZED: self.recognized_passes,
            LearnerState.EXPLAINED: self.explained_passes,
            LearnerState.APPLIED: self.applied_passes,
            LearnerState.TRANSFERRED: self.transferred_passes,
            LearnerState.AUTONOMOUS: self.autonomous_passes,
        }
        try:
            return values[state]
        except KeyError as error:
            raise DomainValidationError("new has no advancement threshold") from error


@dataclass(frozen=True)
class ApprovedObjectFact:
    knowledge_id: str
    knowledge_version: int
    requested_scope: str | None
    unresolved_relevant_contradiction: bool

    def __post_init__(self) -> None:
        _require_text(self.knowledge_id, "knowledge id")
        if self.knowledge_version < 1:
            raise DomainValidationError("knowledge version must be positive")
        _require_optional_text(self.requested_scope, "requested scope")


@dataclass(frozen=True)
class LearnerEvidence:
    id: str
    knowledge_id: str
    knowledge_version: int
    task_ref: str | None
    session_id: str
    criterion: str
    outcome: EvidenceOutcome
    assistance_level: AssistanceLevel
    scope: str | None
    user_contribution: str | None
    proposed_state: LearnerState
    approved_state: LearnerState | None
    is_meaningful_transfer: bool
    approval_receipt_id: str
    created_at: datetime

    def __post_init__(self) -> None:
        for value, name in (
            (self.id, "evidence id"),
            (self.knowledge_id, "knowledge id"),
            (self.session_id, "session id"),
            (self.criterion, "criterion"),
            (self.approval_receipt_id, "approval receipt id"),
        ):
            _require_text(value, name)
        if self.knowledge_version < 1:
            raise DomainValidationError("knowledge version must be positive")
        _require_optional_text(self.task_ref, "task reference")
        _require_optional_text(self.scope, "scope")
        _require_optional_text(self.user_contribution, "user contribution")
        _require_utc(self.created_at, "evidence creation time")
        if (
            self.approved_state is not None
            and _STATE_RANK[self.approved_state] >= _STATE_RANK[LearnerState.APPLIED]
        ):
            if self.task_ref is None:
                raise DomainValidationError("task reference is required for applied evidence")
            if self.assistance_level is AssistanceLevel.UNKNOWN:
                raise DomainValidationError("known assistance is required for applied evidence")
        if self.is_meaningful_transfer and (
            self.approved_state is None
            or _STATE_RANK[self.approved_state] < _STATE_RANK[LearnerState.TRANSFERRED]
        ):
            raise DomainValidationError("meaningful transfer requires transferred evidence")


@dataclass(frozen=True)
class LearnerStateSummary:
    knowledge_id: str
    knowledge_version: int
    scope: str | None
    state: LearnerState
    supporting_evidence_ids: tuple[str, ...]
    excluded_evidence_ids: tuple[str, ...]
    unmet_autonomy_conditions: tuple[str, ...]
    calculated_at: datetime

    def __post_init__(self) -> None:
        _require_text(self.knowledge_id, "knowledge id")
        if self.knowledge_version < 1:
            raise DomainValidationError("knowledge version must be positive")
        _require_optional_text(self.scope, "scope")
        _require_utc(self.calculated_at, "summary calculation time")


@dataclass(frozen=True)
class LearningInspection:
    summary: LearnerStateSummary
    supporting_evidence: tuple[LearnerEvidence, ...]
    excluded_evidence_ids: tuple[str, ...]
    truncated: bool


def approved_object_fact(result: SearchResult, requested_scope: str | None) -> ApprovedObjectFact:
    """Translate the promoted C003 retrieval result into the narrow learning fact."""
    return ApprovedObjectFact(
        result.knowledge_id,
        result.version,
        requested_scope,
        bool(result.conflicts),
    )


def validate_evidence(
    evidence: LearnerEvidence,
    fact: ApprovedObjectFact,
    receipt: ApprovalReceipt,
) -> LearnerEvidence:
    """Validate actual approved-object and receipt binding before a state write."""
    if evidence.knowledge_id != fact.knowledge_id or evidence.knowledge_version != (
        fact.knowledge_version
    ):
        raise DomainValidationError("evidence does not match the approved object/version")
    if evidence.scope != fact.requested_scope:
        raise DomainValidationError("evidence does not match the requested scope")
    if evidence.approval_receipt_id != receipt.operation_id:
        raise DomainValidationError("evidence approval receipt id does not match")
    if receipt.operation_kind is not PendingOperationKind.LEARNING_EVIDENCE:
        raise DomainValidationError("receipt does not authorize learning evidence")
    if (evidence.knowledge_id, evidence.knowledge_version) not in receipt.object_ids_versions:
        raise DomainValidationError("receipt does not bind the evidence object/version")
    return evidence


def _is_applicable(evidence: LearnerEvidence, fact: ApprovedObjectFact) -> bool:
    return (
        evidence.knowledge_id == fact.knowledge_id
        and evidence.knowledge_version == fact.knowledge_version
        and evidence.scope == fact.requested_scope
    )


def _qualifies(evidence: LearnerEvidence, state: LearnerState) -> bool:
    if (
        evidence.outcome is not EvidenceOutcome.PASS
        or evidence.user_contribution is None
        or evidence.approved_state is None
        or evidence.approved_state is LearnerState.NEW
        or _STATE_RANK[evidence.approved_state] < _STATE_RANK[state]
    ):
        return False
    if _STATE_RANK[state] >= _STATE_RANK[LearnerState.APPLIED] and (
        evidence.task_ref is None or evidence.assistance_level is AssistanceLevel.UNKNOWN
    ):
        return False
    return state is not LearnerState.TRANSFERRED or evidence.is_meaningful_transfer


def _autonomy_conditions(
    evidence: tuple[LearnerEvidence, ...],
    threshold: int,
    contradiction: bool,
    agreement: bool,
) -> tuple[str, ...]:
    independent = tuple(
        item
        for item in evidence
        if _qualifies(item, LearnerState.APPLIED)
        and item.assistance_level is AssistanceLevel.INDEPENDENT
    )
    tasks = {item.task_ref for item in independent if item.task_ref is not None}
    sessions = {item.session_id for item in independent}
    unmet: list[str] = []
    if len(independent) < threshold:
        unmet.append("independent_passes")
    if len(tasks) < threshold:
        unmet.append("distinct_tasks")
    if len(sessions) < threshold:
        unmet.append("separate_sessions")
    if not any(item.is_meaningful_transfer for item in independent):
        unmet.append("meaningful_transfer")
    if contradiction:
        unmet.append("relevant_contradiction")
    if not agreement:
        unmet.append("scaffolding_agreement")
    return tuple(unmet)


def summarize_mastery(
    fact: ApprovedObjectFact,
    evidence: tuple[LearnerEvidence, ...],
    thresholds: AdvancementThresholds,
    scaffolding_agreement: bool,
    calculated_at: datetime,
) -> LearnerStateSummary:
    """Return the highest justified state without mutating evidence or configuration."""
    _require_utc(calculated_at, "summary calculation time")
    ids = tuple(item.id for item in evidence)
    if len(ids) != len(set(ids)):
        raise DomainValidationError("duplicate evidence id")
    applicable = tuple(item for item in evidence if _is_applicable(item, fact))
    unmet = _autonomy_conditions(
        applicable,
        thresholds.autonomous_passes,
        fact.unresolved_relevant_contradiction,
        scaffolding_agreement,
    )
    state = LearnerState.NEW
    if not unmet:
        state = LearnerState.AUTONOMOUS
    else:
        for candidate in (
            LearnerState.TRANSFERRED,
            LearnerState.APPLIED,
            LearnerState.EXPLAINED,
            LearnerState.RECOGNIZED,
        ):
            qualifying = tuple(item for item in applicable if _qualifies(item, candidate))
            if len(qualifying) >= thresholds.for_state(candidate):
                state = candidate
                break
    if state is LearnerState.NEW:
        supporting: tuple[LearnerEvidence, ...] = ()
    elif state is LearnerState.AUTONOMOUS:
        supporting = tuple(
            item
            for item in applicable
            if _qualifies(item, LearnerState.APPLIED)
            and item.assistance_level is AssistanceLevel.INDEPENDENT
        )
    else:
        supporting = tuple(item for item in applicable if _qualifies(item, state))
    supporting_ids = tuple(item.id for item in supporting)
    excluded_ids = tuple(item.id for item in evidence if item.id not in set(supporting_ids))
    return LearnerStateSummary(
        fact.knowledge_id,
        fact.knowledge_version,
        fact.requested_scope,
        state,
        supporting_ids,
        excluded_ids,
        unmet,
        calculated_at,
    )


def inspect_learning_state(
    summary: LearnerStateSummary,
    evidence: tuple[LearnerEvidence, ...],
    limit: int,
) -> LearningInspection:
    """Return a bounded deterministic projection of evidence supporting the summary."""
    if not 1 <= limit <= 20:
        raise DomainValidationError("inspection limit must be between 1 and 20")
    by_id = {item.id: item for item in evidence}
    ordered = tuple(
        by_id[identifier] for identifier in summary.supporting_evidence_ids if identifier in by_id
    )
    return LearningInspection(
        summary,
        ordered[:limit],
        summary.excluded_evidence_ids[:limit],
        len(ordered) > limit or len(summary.excluded_evidence_ids) > limit,
    )
