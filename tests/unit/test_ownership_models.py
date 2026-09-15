#!/usr/bin/env python3
# Purpose: Test ownership model invariants and trusted request bindings.

from __future__ import annotations

import json
from dataclasses import fields, replace
from pathlib import Path

import pytest

from expertiseos.ownership import (
    CollisionPolicy,
    ExportRequestBinding,
    KnowledgeRef,
    OwnershipError,
    RestoreRequestBinding,
    SelectionAuthority,
    destination_ref,
    scope_digest,
)
from tests.integration.fixtures.reliability_fixtures import approved_scope, user_event


def test_operation_models_have_no_field_defaults() -> None:
    for model in (KnowledgeRef, ExportRequestBinding, RestoreRequestBinding):
        assert all(field.default is field.default_factory for field in fields(model))


def test_export_binding_seals_scope_destination_and_session(tmp_path: Path) -> None:
    scope = approved_scope()
    destination = tmp_path / "bundle"
    authority = SelectionAuthority(b"x" * 32, "adapter-1", "session-1")
    binding = authority.issue_export(user_event("event-1"), "operation-1", scope, destination)

    assert binding.operation_id == "operation-1"
    assert binding.scope_digest == scope_digest(scope)
    assert binding.destination_ref == destination_ref(destination)
    with pytest.raises(OwnershipError, match="altered"):
        changed = replace(binding, destination_ref="caller-assertion")
        authority.verify_export(changed, scope, destination)


def test_actual_event_is_one_use_and_cross_session_is_rejected(tmp_path: Path) -> None:
    authority = SelectionAuthority(b"x" * 32, "adapter-1", "session-1")
    scope = approved_scope()
    event = user_event("event-1")
    authority.issue_export(event, "operation-1", scope, tmp_path / "one")
    with pytest.raises(OwnershipError, match="already used"):
        authority.issue_export(event, "operation-2", scope, tmp_path / "two")
    with pytest.raises(OwnershipError, match="outside authority session"):
        authority.issue_export(
            user_event("event-2", "other-session"), "operation-3", scope, tmp_path / "three"
        )


def test_restore_policy_is_explicit() -> None:
    assert tuple(CollisionPolicy) == (CollisionPolicy.REJECT_DIVERGENT,)


def test_manifest_schema_allowlist_matches_implementation() -> None:
    from expertiseos.ownership import ALLOWED_RECORD_TYPES

    schema_path = (
        Path(__file__).parents[2]
        / "specs/007-ownership-reliability/contracts/export-manifest.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    allowed = set(schema["properties"]["files"]["items"]["properties"]["record_type"]["enum"])
    assert allowed == ALLOWED_RECORD_TYPES
    assert {"candidate", "decision_grant", "repair_payload"}.isdisjoint(allowed)
