#!/usr/bin/env python3
# Purpose: Test knowledge/service.py preservation of exact approved provenance fields.

from __future__ import annotations

from expertiseos.domain.models import AccessibilityStatus, SourceReference, SourceType
from tests.consent_support import NOW, approved, observation, service_bundle


def test_exact_approved_source_scope_and_contribution_round_trip() -> None:
    bundle = service_bundle()
    value = approved(
        "scoped observation",
        source_refs=("event:host-user-1", "excerpt:approved only", "access:available"),
        contribution_origin="joint",
    )
    bundle.service.propose_create("p", "o", "s", "codex", value, NOW)
    bundle.service.present("p")
    bundle.service.register_decision("p", "g", observation(), NOW)
    result = bundle.service.commit("p", "g", "o")
    assert result.records[0].source_refs == value.source_refs
    assert result.records[0].contribution_origin == "joint"


def test_unavailable_source_is_explicit_and_not_reconstructed() -> None:
    source = SourceReference(
        SourceType.FILE,
        None,
        None,
        None,
        "missing.md",
        None,
        NOW,
        "checksum",
        AccessibilityStatus.UNAVAILABLE,
    )
    assert source.accessibility_status is AccessibilityStatus.UNAVAILABLE
    assert source.approved_excerpt is None
