#!/usr/bin/env python3
# Purpose: Test candidate_store.py and service.py decline, expiry, and restart privacy.

from __future__ import annotations

from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.domain.models import CandidateState
from expertiseos.knowledge.backend import SearchQuery
from tests.consent_support import present_create, service_bundle


def test_decline_suppression_is_session_only_and_volatile() -> None:
    bundle = service_bundle()
    proposal_id, _ = present_create(bundle, "UNAPPROVED_MARKER_74E9")
    result = bundle.service.decline(proposal_id, "fingerprint-1")
    assert result.state is CandidateState.DECLINED
    assert bundle.candidates.is_suppressed("session-1", "fingerprint-1")
    assert not CandidateStore().is_suppressed("session-1", "fingerprint-1")
    assert bundle.receipts.get_receipt("operation-1") is None
    query = SearchQuery("UNAPPROVED_MARKER_74E9", 10, None, (), (), ())
    assert bundle.backend.search(query) == ()


def test_unrelated_message_session_end_and_restart_expire_without_storage() -> None:
    bundle = service_bundle()
    first, _ = present_create(bundle, "marker-one", "p1", "o1")
    second, _ = present_create(bundle, "marker-two", "p2", "o2")
    assert bundle.candidates.expire_unrelated_decisions("session-1", second) == (first,)
    assert bundle.service.expire_session("session-1") == (second,)
    assert bundle.receipts.get_receipt("o1") is None
    assert bundle.receipts.get_receipt("o2") is None
    assert CandidateStore().get(first) is None


def test_unrelated_decision_expiry_removes_its_grant() -> None:
    bundle = service_bundle()
    first, first_grant = present_create(bundle, "marker-one", "p1", "o1")
    second, _ = present_create(
        bundle, "marker-two", "p2", "o2", session_id="session-1", adapter_id="codex"
    )
    assert bundle.service.expire_unrelated_decisions("session-1", second) == (first,)
    assert bundle.grants.get(first_grant) is None
