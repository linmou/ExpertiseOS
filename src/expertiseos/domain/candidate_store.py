#!/usr/bin/env python3
# Purpose: Keep unapproved proposals and decline suppression in process memory only.

from __future__ import annotations

from dataclasses import replace

from expertiseos.domain.errors import CandidateNotFoundError, CandidateTransitionError
from expertiseos.domain.models import CandidateState, PendingOperation


class CandidateStore:
    """Small in-memory state machine with no durable serialization path."""

    def __init__(self) -> None:
        self._proposals: dict[str, PendingOperation] = {}
        self._declined_fingerprints: dict[str, set[str]] = {}

    def create_detected(self, proposal: PendingOperation) -> PendingOperation:
        if proposal.state is not CandidateState.DETECTED:
            raise CandidateTransitionError("new proposal must be detected")
        if proposal.proposal_id in self._proposals:
            raise CandidateTransitionError("proposal id already exists")
        self._proposals[proposal.proposal_id] = proposal
        return proposal

    def get(self, proposal_id: str) -> PendingOperation | None:
        return self._proposals.get(proposal_id)

    def replace_awaiting_decision(self, proposal: PendingOperation) -> PendingOperation:
        current = self._proposals.get(proposal.proposal_id)
        if current is None:
            raise CandidateNotFoundError(proposal.proposal_id)
        if (
            current.state is not CandidateState.AWAITING_DECISION
            or proposal.state is not CandidateState.AWAITING_DECISION
        ):
            raise CandidateTransitionError("only an awaiting decision may be replaced")
        if (
            current.proposal_id != proposal.proposal_id
            or current.operation_id != proposal.operation_id
            or current.session_id != proposal.session_id
            or current.adapter_id != proposal.adapter_id
            or current.kind is not proposal.kind
            or current.expected_versions != proposal.expected_versions
            or current.created_at != proposal.created_at
        ):
            raise CandidateTransitionError("replacement changed immutable proposal binding")
        self._proposals[proposal.proposal_id] = proposal
        return proposal

    def get_active(self, proposal_id: str, session_id: str, adapter_id: str) -> PendingOperation:
        proposal = self._proposals.get(proposal_id)
        if (
            proposal is None
            or proposal.session_id != session_id
            or proposal.adapter_id != adapter_id
        ):
            raise CandidateNotFoundError("active proposal not found")
        if proposal.state in {
            CandidateState.APPROVED,
            CandidateState.DECLINED,
            CandidateState.EXPIRED,
        }:
            raise CandidateTransitionError("proposal is terminal")
        return proposal

    def mark_awaiting_checkpoint(self, proposal_id: str) -> PendingOperation:
        return self._transition(
            proposal_id, CandidateState.DETECTED, CandidateState.AWAITING_CHECKPOINT
        )

    def mark_awaiting_decision(self, proposal_id: str) -> PendingOperation:
        return self._transition(
            proposal_id,
            CandidateState.AWAITING_CHECKPOINT,
            CandidateState.AWAITING_DECISION,
        )

    def mark_approved(self, proposal_id: str) -> PendingOperation:
        return self._transition(
            proposal_id, CandidateState.AWAITING_DECISION, CandidateState.APPROVED
        )

    def decline(self, proposal_id: str, fingerprint: str | None) -> PendingOperation:
        if fingerprint is not None and not fingerprint:
            raise CandidateTransitionError("decline fingerprint cannot be blank")
        proposal = self._terminate(proposal_id, CandidateState.DECLINED)
        if fingerprint is not None:
            self._declined_fingerprints.setdefault(proposal.session_id, set()).add(fingerprint)
        return proposal

    def expire(self, proposal_id: str) -> PendingOperation:
        return self._terminate(proposal_id, CandidateState.EXPIRED)

    def expire_session(self, session_id: str) -> tuple[str, ...]:
        expired: list[str] = []
        for proposal in tuple(self._proposals.values()):
            if proposal.session_id == session_id and proposal.state not in {
                CandidateState.APPROVED,
                CandidateState.DECLINED,
                CandidateState.EXPIRED,
            }:
                self.expire(proposal.proposal_id)
                expired.append(proposal.proposal_id)
        self._declined_fingerprints.pop(session_id, None)
        return tuple(expired)

    def expire_unrelated_decisions(
        self, session_id: str, active_proposal_id: str | None
    ) -> tuple[str, ...]:
        expired: list[str] = []
        for proposal in tuple(self._proposals.values()):
            if (
                proposal.session_id == session_id
                and proposal.state is CandidateState.AWAITING_DECISION
                and proposal.proposal_id != active_proposal_id
            ):
                self.expire(proposal.proposal_id)
                expired.append(proposal.proposal_id)
        return tuple(expired)

    def is_suppressed(self, session_id: str, fingerprint: str) -> bool:
        return fingerprint in self._declined_fingerprints.get(session_id, set())

    def _transition(
        self,
        proposal_id: str,
        expected: CandidateState,
        target: CandidateState,
    ) -> PendingOperation:
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            raise CandidateNotFoundError(proposal_id)
        if proposal.state is not expected:
            raise CandidateTransitionError(f"cannot transition {proposal.state} to {target}")
        updated = replace(proposal, state=target)
        self._proposals[proposal_id] = updated
        return updated

    def _terminate(self, proposal_id: str, target: CandidateState) -> PendingOperation:
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            raise CandidateNotFoundError(proposal_id)
        if proposal.state in {
            CandidateState.APPROVED,
            CandidateState.DECLINED,
            CandidateState.EXPIRED,
        }:
            raise CandidateTransitionError("terminal proposal cannot transition")
        updated = replace(proposal, state=target)
        self._proposals[proposal_id] = updated
        return updated
