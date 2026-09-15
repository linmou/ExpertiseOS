#!/usr/bin/env python3
# Purpose: Test src/expertiseos/knowledge/backend.py and its deterministic fake contract.

from __future__ import annotations

import hashlib
from dataclasses import MISSING, fields
from datetime import UTC, datetime, timedelta

import pytest

from expertiseos.knowledge.backend import (
    ApprovedKnowledgeInput,
    BackendContractError,
    IdempotencyConflictError,
    IndexState,
    KnowledgeBackend,
    KnowledgeStatus,
    RelationshipInput,
    SearchMode,
    SearchQuery,
    StoreState,
    VersionConflictError,
)
from tests.fakes import DeterministicClock, DeterministicIdGenerator, FakeKnowledgeBackend


def approved(content: str, scope: str | None = None) -> ApprovedKnowledgeInput:
    return ApprovedKnowledgeInput(
        content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
        ("procedure",),
        ("domain",),
        scope,
        "observed",
        ("host-event-1",),
        "user",
    )


def backend(
    index_state: IndexState = IndexState.READY,
    search_mode: SearchMode = SearchMode.KEYWORD,
) -> FakeKnowledgeBackend:
    clock = DeterministicClock(datetime(2026, 9, 14, tzinfo=UTC), timedelta(seconds=1))
    ids = DeterministicIdGenerator("knowledge", 1)
    return FakeKnowledgeBackend(clock, ids, StoreState.READY, index_state, search_mode)


def test_required_dataclass_fields_have_no_defaults() -> None:
    for data_type in (ApprovedKnowledgeInput, RelationshipInput, SearchQuery):
        assert all(field.default is MISSING for field in fields(data_type))
        assert all(field.default_factory is MISSING for field in fields(data_type))


def test_approved_input_validates_digest_subject_and_origin() -> None:
    with pytest.raises(BackendContractError, match="digest"):
        ApprovedKnowledgeInput("content", "wrong", (), ("domain",), None, None, (), "user")
    with pytest.raises(BackendContractError, match="subject"):
        ApprovedKnowledgeInput(
            "content",
            hashlib.sha256(b"content").hexdigest(),
            (),
            (),
            None,
            None,
            (),
            "user",
        )
    with pytest.raises(BackendContractError, match="origin"):
        ApprovedKnowledgeInput(
            "content",
            hashlib.sha256(b"content").hexdigest(),
            (),
            ("domain",),
            None,
            None,
            (),
            "unknown",
        )


def test_create_current_historical_update_and_versions() -> None:
    store = backend()
    assert isinstance(store, KnowledgeBackend)
    first = store.create_approved(approved("first"), "operation-create")
    second = store.update_approved(first.id, 1, approved("second"), "operation-update")
    assert store.get(first.id) == second
    assert store.get(first.id, 1) == first
    assert store.get_current_versions((first.id, "missing")) == {first.id: 2}


def test_search_is_bounded_scoped_and_reports_degraded_mode() -> None:
    store = backend(IndexState.DEGRADED, SearchMode.KEYWORD)
    store.create_approved(approved("retry safely", "python"), "operation-1")
    store.create_approved(approved("retry elsewhere", "rust"), "operation-2")
    results = store.search(SearchQuery("retry", 1, "python", (), (), ()))
    assert len(results) == 1
    assert results[0].excerpt == "retry safely"
    assert results[0].match_mode is SearchMode.KEYWORD
    assert results[0].index_state is IndexState.DEGRADED


def test_update_replay_conflict_and_new_operation_version_check() -> None:
    store = backend()
    first = store.create_approved(approved("first"), "create")
    value = approved("second")
    updated = store.update_approved(first.id, 1, value, "update")
    assert store.update_approved(first.id, 1, value, "update") == updated
    with pytest.raises(IdempotencyConflictError):
        store.update_approved(first.id, 1, approved("different"), "update")
    with pytest.raises(VersionConflictError):
        store.update_approved(first.id, 1, value, "new-update")


def test_relationship_replay_conflict_and_version_checks() -> None:
    store = backend()
    source = store.create_approved(approved("source"), "create-source")
    target = store.create_approved(approved("target"), "create-target")
    relation = RelationshipInput(source.id, 1, target.id, 1, "supports", None, "event-1")
    result = store.set_relationships((relation,), {source.id: 1, target.id: 1}, "relate")
    assert store.set_relationships((relation,), {source.id: 1, target.id: 1}, "relate") == result
    with pytest.raises(IdempotencyConflictError):
        store.set_relationships((), {source.id: 1}, "relate")
    with pytest.raises(VersionConflictError):
        store.set_relationships((relation,), {source.id: 1}, "new-relate")


def test_retire_visibility_replay_and_conflict() -> None:
    store = backend()
    record = store.create_approved(approved("retire me"), "create")
    retired = store.retire(record.id, 1, "retire")
    assert retired.status is KnowledgeStatus.RETIRED
    assert store.get(record.id) is None
    assert store.get(record.id, 2, include_retired=True) == retired
    assert store.get(record.id, 1) == record
    assert store.retire(record.id, 1, "retire") == retired
    with pytest.raises(IdempotencyConflictError):
        store.retire(record.id, 2, "retire")


def test_delete_requires_version_and_replays_after_removal() -> None:
    store = backend()
    record = store.create_approved(approved("delete me"), "create")
    with pytest.raises(VersionConflictError):
        store.delete(record.id, 2, "wrong-delete")
    deleted = store.delete(record.id, 1, "delete")
    assert deleted.deleted_versions == 1
    assert store.get(record.id, 1, include_retired=True) is None
    assert store.delete(record.id, 1, "delete") == deleted
    with pytest.raises(IdempotencyConflictError):
        store.delete("different", 1, "delete")


def test_create_replay_does_not_allocate_another_identity() -> None:
    store = backend()
    value = approved("same")
    first = store.create_approved(value, "create")
    assert store.create_approved(value, "create") == first
    with pytest.raises(IdempotencyConflictError):
        store.create_approved(approved("different"), "create")
    second = store.create_approved(value, "create-next")
    assert second.id == "knowledge-2"


def test_rebuild_is_non_semantic_and_health_is_separate() -> None:
    store = backend(IndexState.UNAVAILABLE, SearchMode.KEYWORD)
    store.create_approved(approved("indexed"), "create")
    assert store.health().canonical_store is StoreState.READY
    assert store.health().index is IndexState.UNAVAILABLE
    rebuilt = store.rebuild_index()
    assert rebuilt.indexed_records == 1
    assert rebuilt.index_state is IndexState.READY


def test_fake_rejects_non_approved_input() -> None:
    store = backend()
    with pytest.raises(TypeError, match="ApprovedKnowledgeInput"):
        store.create_approved(object(), "operation")  # type: ignore[arg-type]
