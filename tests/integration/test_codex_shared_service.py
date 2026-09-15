#!/usr/bin/env python3
# Purpose: Test src/expertiseos/hosts/codex.py consumes actual shared retrieval outputs.

import pytest

from expertiseos.hosts.codex import try_optional_call
from expertiseos.knowledge.backend import SearchMode, SearchQuery, TrustLevel
from tests.backend_support import approved
from tests.consent_support import service_bundle

pytestmark = pytest.mark.integration


def test_codex_side_read_preserves_shared_identity_and_untrusted_status() -> None:
    bundle = service_bundle()
    created = bundle.backend.create_approved(
        approved("shared Codex recall", None, ("fact",), ("domain",), ("event:1",)),
        "create-shared",
    )

    optional = try_optional_call(
        lambda: bundle.service.search(SearchQuery("Codex recall", 3, None, (), (), ()))
    )

    assert optional.available
    response = optional.value
    assert response is not None
    assert response.results[0].knowledge_id == created.id
    assert response.results[0].version == created.version
    assert response.results[0].trust is TrustLevel.UNTRUSTED_DATA
    assert response.mode is SearchMode.KEYWORD


def test_codex_side_get_returns_same_approved_version() -> None:
    bundle = service_bundle()
    created = bundle.backend.create_approved(
        approved("stable identity", None, ("fact",), ("domain",), ("event:2",)),
        "create-stable",
    )
    optional = try_optional_call(lambda: bundle.service.get(created.id, None, False))
    assert optional.value == created
