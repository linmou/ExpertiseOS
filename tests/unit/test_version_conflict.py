#!/usr/bin/env python3
# Purpose: Test knowledge/service.py optimistic versions and deterministic grouped replay.

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from expertiseos.approval.gate import ApprovalGate, child_operation_id
from expertiseos.domain.models import (
    ApprovalReceipt,
    CommitStatus,
    CreateOperation,
    PendingOperationKind,
)
from expertiseos.knowledge.backend import ApprovedKnowledgeInput, KnowledgeRecord
from expertiseos.knowledge.service import KnowledgeService
from expertiseos.state.sqlite import SQLiteState
from tests.consent_support import (
    NOW,
    ServiceBundle,
    approved,
    fake_backend,
    observation,
    service_bundle,
)
from tests.fakes import FakeKnowledgeBackend


class BeforeWriteFailureBackend(FakeKnowledgeBackend):
    def __init__(self, delegate: FakeKnowledgeBackend) -> None:
        self.__dict__.update(delegate.__dict__)
        self.fail_update = True

    def update_approved(
        self,
        knowledge_id: str,
        expected_version: int,
        value: ApprovedKnowledgeInput,
        operation_id: str,
    ) -> KnowledgeRecord:
        if self.fail_update:
            self.fail_update = False
            raise OSError("injected before-write failure")
        return super().update_approved(knowledge_id, expected_version, value, operation_id)


class CaptureCreateBackend(FakeKnowledgeBackend):
    def __init__(self, delegate: FakeKnowledgeBackend) -> None:
        self.__dict__.update(delegate.__dict__)
        self.operation_ids: list[str] = []

    def create_approved(self, value: ApprovedKnowledgeInput, operation_id: str) -> KnowledgeRecord:
        self.operation_ids.append(operation_id)
        return super().create_approved(value, operation_id)


class TamperSecondGroupedCreateBackend(FakeKnowledgeBackend):
    def __init__(self, delegate: FakeKnowledgeBackend) -> None:
        self.__dict__.update(delegate.__dict__)
        self.create_count = 0

    def create_approved(self, value: ApprovedKnowledgeInput, operation_id: str) -> KnowledgeRecord:
        self.create_count += 1
        record = super().create_approved(value, operation_id)
        if self.create_count == 2:
            tampered = replace(record, content="tampered child")
            self._history[record.id][-1] = tampered
            return tampered
        return record


class FailOnceReceiptStore:
    def __init__(self, delegate: SQLiteState) -> None:
        self.delegate = delegate
        self.failed = False

    def get_receipt(self, operation_id: str) -> ApprovalReceipt | None:
        return self.delegate.get_receipt(operation_id)

    def record_receipt(self, receipt: ApprovalReceipt) -> ApprovalReceipt:
        if not self.failed:
            self.failed = True
            raise OSError("injected receipt failure")
        return self.delegate.record_receipt(receipt)


def register(bundle: ServiceBundle, proposal_id: str, grant_id: str) -> None:
    bundle.service.present(proposal_id)
    bundle.service.register_decision(
        proposal_id,
        grant_id,
        observation(user_event_ref=f"host-user-event-{proposal_id}"),
        NOW,
    )


def test_concurrent_revision_uses_optimistic_conflict() -> None:
    bundle = service_bundle()
    first = bundle.backend.create_approved(approved("v1"), "seed")
    for proposal_id, operation_id, content in (("p1", "o1", "v2"), ("p2", "o2", "v3")):
        bundle.service.propose_revision(
            proposal_id, operation_id, "s", "codex", first.id, 1, approved(content), NOW
        )
        register(bundle, proposal_id, f"g-{proposal_id}")
    assert bundle.service.commit("p1", "g-p1", "o1").status is CommitStatus.COMMITTED
    assert bundle.service.commit("p2", "g-p2", "o2").status is CommitStatus.CONFLICT
    assert bundle.backend.get(first.id).content == "v2"  # type: ignore[union-attr]


def test_before_write_failure_then_external_version_change_stays_conflict() -> None:
    backend = BeforeWriteFailureBackend(fake_backend())
    first = backend.create_approved(approved("v1"), "seed")
    bundle = service_bundle(backend)
    bundle.service.propose_revision(
        "p", "retry-op", "s", "codex", first.id, 1, approved("candidate-v2"), NOW
    )
    register(bundle, "p", "g")
    assert bundle.service.commit("p", "g", "retry-op").status is CommitStatus.FAILED
    FakeKnowledgeBackend.update_approved(
        backend, first.id, 1, approved("external-v2"), "external-op"
    )
    assert bundle.service.commit("p", "g", "retry-op").status is CommitStatus.CONFLICT
    assert backend.get(first.id).content == "external-v2"  # type: ignore[union-attr]


def test_retirement_increments_version_without_deleting_history() -> None:
    bundle = service_bundle()
    first = bundle.backend.create_approved(approved("keep history"), "seed")
    bundle.service.propose_retirement("p", "retire-op", "s", "codex", first.id, 1, NOW)
    register(bundle, "p", "g")
    result = bundle.service.commit("p", "g", "retire-op")
    assert result.status is CommitStatus.COMMITTED
    assert result.records[0].version == 2
    assert bundle.backend.get(first.id) is None
    assert bundle.backend.get(first.id, 1) == first


def test_grouped_effects_reuse_deterministic_child_operation_ids() -> None:
    backend = CaptureCreateBackend(fake_backend())
    bundle = service_bundle(backend)
    receipts = FailOnceReceiptStore(bundle.receipts)
    service = KnowledgeService(
        backend,
        bundle.candidates,
        bundle.grants,
        ApprovalGate(),
        receipts,
        lambda: NOW + timedelta(hours=2),
    )
    effects = (CreateOperation(approved("left")), CreateOperation(approved("right")))
    service.propose_grouped(
        "p",
        "parent",
        "s",
        "codex",
        PendingOperationKind.CONFLICT_RESOLUTION,
        effects,
        {},
        NOW,
    )
    service.present("p")
    service.register_decision("p", "g", observation(), NOW)
    assert service.commit("p", "g", "parent").status is CommitStatus.INCOMPLETE
    result = service.commit("p", "g", "parent")
    assert result.status is CommitStatus.COMMITTED
    expected = [
        child_operation_id("parent", 0, "CreateOperation"),
        child_operation_id("parent", 1, "CreateOperation"),
    ]
    assert backend.operation_ids == expected + expected
    assert len(result.records) == 2


def test_grouped_commit_validates_each_child_against_approved_effect() -> None:
    backend = TamperSecondGroupedCreateBackend(fake_backend())
    bundle = service_bundle(backend)
    effects = (CreateOperation(approved("left")), CreateOperation(approved("right")))
    bundle.service.propose_grouped(
        "p",
        "parent",
        "s",
        "codex",
        PendingOperationKind.CONFLICT_RESOLUTION,
        effects,
        {},
        NOW,
    )
    register(bundle, "p", "g")
    result = bundle.service.commit("p", "g", "parent")
    assert result.status is CommitStatus.FAILED
    assert result.error_code == "ReadBackMismatchError"
    assert bundle.receipts.get_receipt("parent") is None
