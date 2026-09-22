#!/usr/bin/env python3
# Purpose: Test approval/gate.py proposal, adapter, and session isolation.

from __future__ import annotations

import pytest

from expertiseos.domain.errors import ApprovalRejectedError
from expertiseos.domain.models import CommitStatus
from tests.consent_support import NOW, approved, observation, service_bundle


def test_grant_for_proposal_a_cannot_commit_proposal_b() -> None:
    bundle = service_bundle()
    for proposal_id, operation_id in (("a", "oa"), ("b", "ob")):
        bundle.service.propose_create(
            proposal_id,
            operation_id,
            "session-1",
            "codex",
            approved(proposal_id),
            NOW,
        )
        bundle.service.present(proposal_id)
    bundle.service.register_decision("a", "grant-a", observation(), NOW)
    assert bundle.service.commit("b", "grant-a", "ob").status is CommitStatus.REJECTED
    assert bundle.backend.get_current_versions(()) == {}


def test_codex_session_grant_cannot_cross_to_claude_session() -> None:
    bundle = service_bundle()
    bundle.service.propose_create("codex-p", "codex-o", "codex-s", "codex", approved("a"), NOW)
    bundle.service.present("codex-p")
    bundle.service.register_decision("codex-p", "codex-g", observation(), NOW)
    bundle.service.propose_create("claude-p", "claude-o", "claude-s", "claude", approved("b"), NOW)
    bundle.service.present("claude-p")
    assert bundle.service.commit("claude-p", "codex-g", "claude-o").status is (
        CommitStatus.REJECTED
    )


def test_one_user_event_cannot_grant_two_proposals() -> None:
    bundle = service_bundle()
    for proposal_id in ("a", "b"):
        bundle.service.propose_create(
            proposal_id, f"o-{proposal_id}", "session-1", "codex", approved(proposal_id), NOW
        )
        bundle.service.present(proposal_id)
    bundle.service.register_decision("a", "grant-a", observation(), NOW)
    with pytest.raises(ApprovalRejectedError, match="already granted"):
        bundle.service.register_decision("b", "grant-b", observation(), NOW)
