#!/usr/bin/env python3
# Purpose: Test src/expertiseos/domain/models.py explicit fields and validation rules.

from __future__ import annotations

import hashlib
from dataclasses import MISSING, fields
from datetime import datetime, timedelta, timezone

import pytest

from expertiseos.domain.errors import DomainValidationError
from expertiseos.domain.models import (
    AccessibilityStatus,
    ApprovalReceipt,
    CandidateState,
    CommitResult,
    CreateOperation,
    DecisionGrant,
    GroupedOperation,
    KnowledgeCategory,
    KnowledgeSubject,
    LearnerState,
    PendingOperation,
    PendingOperationKind,
    Relationship,
    RelationType,
    RetireOperation,
    SourceReference,
    SourceType,
)
from tests.consent_support import NOW, approved


def test_all_consent_dataclasses_require_every_field() -> None:
    types = (
        SourceReference,
        Relationship,
        CreateOperation,
        RetireOperation,
        GroupedOperation,
        PendingOperation,
        DecisionGrant,
        ApprovalReceipt,
        CommitResult,
    )
    for data_type in types:
        assert all(item.default is MISSING for item in fields(data_type))
        assert all(item.default_factory is MISSING for item in fields(data_type))


def test_required_enum_values_are_stable() -> None:
    assert len(KnowledgeCategory) == 6
    assert {item.value for item in KnowledgeSubject} == {"domain", "self", "ai"}
    assert len(RelationType) == 7
    assert list(LearnerState)[0].value == "new"
    assert list(LearnerState)[-1].value == "autonomous"


def test_pending_operation_rejects_bad_digest_versions_and_non_utc_time() -> None:
    payload = CreateOperation(approved("content"))
    with pytest.raises(DomainValidationError, match="SHA-256"):
        PendingOperation(
            "p",
            "o",
            "s",
            "a",
            PendingOperationKind.CREATE,
            CandidateState.DETECTED,
            payload,
            "wrong",
            (),
            NOW,
        )
    digest = hashlib.sha256(b"digest").hexdigest()
    with pytest.raises(DomainValidationError, match="uniquely sorted"):
        PendingOperation(
            "p",
            "o",
            "s",
            "a",
            PendingOperationKind.CREATE,
            CandidateState.DETECTED,
            payload,
            digest,
            (("z", 1), ("a", 1)),
            NOW,
        )
    with pytest.raises(DomainValidationError, match="UTC"):
        PendingOperation(
            "p",
            "o",
            "s",
            "a",
            PendingOperationKind.CREATE,
            CandidateState.DETECTED,
            payload,
            digest,
            (),
            datetime(2026, 9, 14, tzinfo=timezone(timedelta(hours=1))),
        )


def test_source_and_relationship_validate_versions_and_excerpt() -> None:
    with pytest.raises(DomainValidationError, match="excerpt"):
        SourceReference(
            SourceType.FILE,
            None,
            None,
            None,
            "file.py",
            " ",
            None,
            None,
            AccessibilityStatus.AVAILABLE,
        )
    with pytest.raises(DomainValidationError, match="positive"):
        Relationship("r", "a", 0, "b", 1, RelationType.SUPPORTS, None, None)


def test_retirement_is_distinct_from_delete_operation_kind() -> None:
    assert {PendingOperationKind.RETIRE.value, PendingOperationKind.DELETE.value} == {
        "retire",
        "delete",
    }
    with pytest.raises(DomainValidationError, match="positive"):
        RetireOperation("knowledge-1", 0)
