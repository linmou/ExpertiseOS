#!/usr/bin/env python3
# Purpose: Test knowledge/service.py exact relationship approval and conflict preservation.

from __future__ import annotations

import pytest

from expertiseos.domain.models import CommitStatus
from expertiseos.knowledge.backend import RelationshipInput
from tests.consent_support import NOW, approved, observation, service_bundle


def test_approved_relationship_round_trips_with_provenance() -> None:
    bundle = service_bundle()
    source = bundle.backend.create_approved(approved("general retry"), "seed-source")
    target = bundle.backend.create_approved(approved("side effects differ"), "seed-target")
    relation = RelationshipInput(
        source.id, 1, target.id, 1, "contradicts", "different boundary", "event-rel"
    )
    bundle.service.propose_relation_change(
        "p", "rel-op", "s", "codex", (relation,), {source.id: 1, target.id: 1}, NOW
    )
    bundle.service.present("p")
    bundle.service.register_decision("p", "g", observation(), NOW)
    result = bundle.service.commit("p", "g", "rel-op")
    assert result.status is CommitStatus.COMMITTED
    stored = bundle.backend.get(source.id, 2)
    assert stored is not None and stored.relationships == (relation,)
    assert bundle.backend.get(target.id, 1) == target


def test_unapproved_relationship_makes_no_change() -> None:
    bundle = service_bundle()
    source = bundle.backend.create_approved(approved("source"), "seed-source")
    target = bundle.backend.create_approved(approved("target"), "seed-target")
    relation = RelationshipInput(source.id, 1, target.id, 1, "supports", None, None)
    bundle.service.propose_relation_change(
        "p", "rel-op", "s", "codex", (relation,), {source.id: 1, target.id: 1}, NOW
    )
    bundle.service.present("p")
    assert bundle.service.commit("p", "missing", "rel-op").status is CommitStatus.REJECTED
    assert bundle.backend.get(source.id, 1).relationships == ()  # type: ignore[union-attr]


def test_unsupported_type_or_unbound_endpoint_version_is_rejected() -> None:
    bundle = service_bundle()
    bad = RelationshipInput("source", 1, "target", 1, "invented", None, None)
    with pytest.raises(ValueError, match="unsupported"):
        bundle.service.propose_relation_change(
            "p", "o", "s", "codex", (bad,), {"source": 1, "target": 1}, NOW
        )
    supported = RelationshipInput("source", 1, "target", 1, "supports", None, None)
    with pytest.raises(ValueError, match="target version"):
        bundle.service.propose_relation_change(
            "p", "o", "s", "codex", (supported,), {"source": 1}, NOW
        )
