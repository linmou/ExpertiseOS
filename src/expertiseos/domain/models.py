#!/usr/bin/env python3
# Purpose: Define explicit-field domain records for consent-bound knowledge operations.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from expertiseos.domain.errors import DomainValidationError
from expertiseos.knowledge.backend import (
    ApprovedKnowledgeInput,
    KnowledgeRecord,
    RelationshipInput,
)
from expertiseos.knowledge.backend import (
    KnowledgeStatus as BackendKnowledgeStatus,
)

type KnowledgeObject = KnowledgeRecord
KnowledgeStatus = BackendKnowledgeStatus


class KnowledgeCategory(StrEnum):
    DECLARATIVE = "declarative"
    STRUCTURAL_PROCEDURAL = "structural_procedural"
    CONDITIONAL_BOUNDARY = "conditional_boundary"
    CAUSAL_MECHANISTIC = "causal_mechanistic"
    EPISODIC_TACIT_EXPERIENTIAL = "episodic_tacit_experiential"
    GOAL_METACOGNITIVE_NORMATIVE = "goal_metacognitive_normative"


class KnowledgeSubject(StrEnum):
    DOMAIN = "domain"
    SELF = "self"
    AI = "ai"


class ContributionOrigin(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    JOINT = "joint"


class RelationType(StrEnum):
    DERIVED_FROM = "derived_from"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    EXPLAINS = "explains"
    EXAMPLE_OF = "example_of"
    APPLIES_WHEN = "applies_when"
    DEPENDS_ON = "depends_on"


class CandidateState(StrEnum):
    DETECTED = "detected"
    AWAITING_CHECKPOINT = "awaiting_checkpoint"
    AWAITING_DECISION = "awaiting_decision"
    APPROVED = "approved"
    DECLINED = "declined"
    EXPIRED = "expired"


class PendingOperationKind(StrEnum):
    CREATE = "create"
    REVISE = "revise"
    RELATION = "relation"
    CONFLICT_RESOLUTION = "conflict_resolution"
    LEARNING_EVIDENCE = "learning_evidence"
    RETIRE = "retire"
    DELETE = "delete"
    CONTROL_CHANGE = "control_change"


class UserDecisionAction(StrEnum):
    SAVE = "save"
    EDIT = "edit"
    SKIP = "skip"
    CONFIRM_CHANGE = "confirm_change"


class LearnerState(StrEnum):
    NEW = "new"
    RECOGNIZED = "recognized"
    EXPLAINED = "explained"
    APPLIED = "applied"
    TRANSFERRED = "transferred"
    AUTONOMOUS = "autonomous"


class SourceType(StrEnum):
    HOST_EVENT = "host_event"
    CONVERSATION = "conversation"
    FILE = "file"
    ARTIFACT = "artifact"
    TOOL_RESULT = "tool_result"
    USER_REFLECTION = "user_reflection"


class AccessibilityStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class CommitStatus(StrEnum):
    COMMITTED = "committed"
    REJECTED = "rejected"
    CONFLICT = "conflict"
    FAILED = "failed"
    INCOMPLETE = "incomplete"


def _require_text(value: str, name: str) -> None:
    if not value or not value.strip():
        raise DomainValidationError(f"{name} is required")


def _require_utc(value: datetime, name: str) -> None:
    offset = value.utcoffset()
    if value.tzinfo is None or offset is None or offset.total_seconds() != 0:
        raise DomainValidationError(f"{name} must be UTC")


def _require_digest(value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise DomainValidationError("content digest must be lowercase SHA-256")


@dataclass(frozen=True)
class SourceReference:
    source_type: SourceType
    host: str | None
    session_id: str | None
    event_ref: str | None
    artifact_locator: str | None
    approved_excerpt: str | None
    date: datetime | None
    checksum: str | None
    accessibility_status: AccessibilityStatus

    def __post_init__(self) -> None:
        if self.date is not None:
            _require_utc(self.date, "source date")
        if self.approved_excerpt is not None and not self.approved_excerpt.strip():
            raise DomainValidationError("approved excerpt cannot be blank")


@dataclass(frozen=True)
class Relationship:
    id: str
    source_id: str
    source_version: int | None
    target_id: str
    target_version: int | None
    type: RelationType
    explanation: str | None
    source_ref: SourceReference | None

    def __post_init__(self) -> None:
        _require_text(self.id, "relationship id")
        _require_text(self.source_id, "relationship source")
        _require_text(self.target_id, "relationship target")
        for version in (self.source_version, self.target_version):
            if version is not None and version < 1:
                raise DomainValidationError("relationship versions must be positive")


@dataclass(frozen=True)
class CreateOperation:
    value: ApprovedKnowledgeInput


@dataclass(frozen=True)
class RevisionOperation:
    knowledge_id: str
    expected_version: int
    value: ApprovedKnowledgeInput

    def __post_init__(self) -> None:
        _require_text(self.knowledge_id, "knowledge id")
        if self.expected_version < 1:
            raise DomainValidationError("expected version must be positive")


@dataclass(frozen=True)
class RelationshipOperation:
    relationships: tuple[RelationshipInput, ...]
    expected_versions: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        _validate_versions(self.expected_versions)
        if not self.relationships:
            raise DomainValidationError("at least one relationship is required")


@dataclass(frozen=True)
class RetireOperation:
    knowledge_id: str
    expected_version: int

    def __post_init__(self) -> None:
        _require_text(self.knowledge_id, "knowledge id")
        if self.expected_version < 1:
            raise DomainValidationError("expected version must be positive")


@dataclass(frozen=True)
class LearningEvidenceOperation:
    value: object


@dataclass(frozen=True)
class ControlChangeOperation:
    value: object


@dataclass(frozen=True)
class DeleteOperation:
    value: object


MutationEffect = CreateOperation | RevisionOperation | RelationshipOperation | RetireOperation
DelegatedOperation = LearningEvidenceOperation | ControlChangeOperation | DeleteOperation


@dataclass(frozen=True)
class GroupedOperation:
    effects: tuple[MutationEffect, ...]

    def __post_init__(self) -> None:
        if not self.effects:
            raise DomainValidationError("grouped operation requires effects")


OperationPayload = MutationEffect | GroupedOperation | DelegatedOperation


def _validate_versions(values: tuple[tuple[str, int], ...]) -> None:
    keys = [key for key, _ in values]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise DomainValidationError("expected versions must be uniquely sorted")
    if any(not key or version < 1 for key, version in values):
        raise DomainValidationError("expected versions require ids and positive versions")


@dataclass(frozen=True)
class PendingOperation:
    proposal_id: str
    operation_id: str
    session_id: str
    adapter_id: str
    kind: PendingOperationKind
    state: CandidateState
    payload: OperationPayload
    content_digest: str
    expected_versions: tuple[tuple[str, int], ...]
    created_at: datetime

    def __post_init__(self) -> None:
        for value, name in (
            (self.proposal_id, "proposal id"),
            (self.operation_id, "operation id"),
            (self.session_id, "session id"),
            (self.adapter_id, "adapter id"),
            (self.content_digest, "content digest"),
        ):
            _require_text(value, name)
        _validate_versions(self.expected_versions)
        _require_digest(self.content_digest)
        _require_utc(self.created_at, "proposal creation time")


@dataclass(frozen=True)
class DecisionGrant:
    grant_id: str
    proposal_id: str
    session_id: str
    adapter_id: str
    action: UserDecisionAction
    content_digest: str
    expected_versions: tuple[tuple[str, int], ...]
    user_event_ref: str
    created_at: datetime
    consumed_at: datetime | None

    def __post_init__(self) -> None:
        for value, name in (
            (self.grant_id, "grant id"),
            (self.proposal_id, "proposal id"),
            (self.session_id, "session id"),
            (self.adapter_id, "adapter id"),
            (self.content_digest, "content digest"),
            (self.user_event_ref, "user event reference"),
        ):
            _require_text(value, name)
        _validate_versions(self.expected_versions)
        _require_digest(self.content_digest)
        _require_utc(self.created_at, "grant creation time")
        if self.consumed_at is not None:
            _require_utc(self.consumed_at, "grant consumption time")


@dataclass(frozen=True)
class ApprovalReceipt:
    operation_id: str
    proposal_id: str
    operation_kind: PendingOperationKind
    object_ids_versions: tuple[tuple[str, int], ...]
    content_digest: str
    user_event_ref: str
    adapter_id: str
    created_at: datetime

    def __post_init__(self) -> None:
        for value, name in (
            (self.operation_id, "operation id"),
            (self.proposal_id, "proposal id"),
            (self.content_digest, "content digest"),
            (self.user_event_ref, "user event reference"),
            (self.adapter_id, "adapter id"),
        ):
            _require_text(value, name)
        _validate_versions(self.object_ids_versions)
        _require_digest(self.content_digest)
        _require_utc(self.created_at, "receipt creation time")


@dataclass(frozen=True)
class AuthorizedOperation:
    grant_id: str
    proposal_id: str
    operation_id: str
    session_id: str
    adapter_id: str
    kind: PendingOperationKind
    payload: DelegatedOperation
    content_digest: str
    expected_versions: tuple[tuple[str, int], ...]
    user_event_ref: str
    existing_receipt: ApprovalReceipt | None

    def __post_init__(self) -> None:
        for value, name in (
            (self.grant_id, "grant id"),
            (self.proposal_id, "proposal id"),
            (self.operation_id, "operation id"),
            (self.session_id, "session id"),
            (self.adapter_id, "adapter id"),
            (self.content_digest, "content digest"),
            (self.user_event_ref, "user event reference"),
        ):
            _require_text(value, name)
        _validate_versions(self.expected_versions)
        _require_digest(self.content_digest)
        expected_type: type[object]
        if self.kind is PendingOperationKind.LEARNING_EVIDENCE:
            expected_type = LearningEvidenceOperation
        elif self.kind is PendingOperationKind.CONTROL_CHANGE:
            expected_type = ControlChangeOperation
        elif self.kind is PendingOperationKind.DELETE:
            expected_type = DeleteOperation
        else:
            raise DomainValidationError("authorization kind is not delegated")
        if not isinstance(self.payload, expected_type):
            raise DomainValidationError("authorization payload does not match operation kind")


@dataclass(frozen=True)
class CommitResult:
    status: CommitStatus
    records: tuple[KnowledgeRecord, ...]
    receipt: ApprovalReceipt | None
    error_code: str | None
