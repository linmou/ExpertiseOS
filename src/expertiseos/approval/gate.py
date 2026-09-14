#!/usr/bin/env python3
# Purpose: Bind actual-user decisions to canonical proposal content and versions.

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass, replace
from datetime import datetime
from enum import Enum

from expertiseos.domain.errors import ApprovalRejectedError, StaleVersionError
from expertiseos.domain.models import (
    CandidateState,
    DecisionGrant,
    PendingOperation,
    PendingOperationKind,
    UserDecisionAction,
)
from expertiseos.hosts.contract import DecisionObservation


def _canonical_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        document: dict[str, object] = {}
        for item in fields(value):
            field_value = getattr(value, item.name)
            if item.name in {"categories", "subjects"}:
                field_value = tuple(sorted(field_value))
            document[item.name] = _canonical_value(field_value)
        return document
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(value[key]) for key in sorted(value)}
    if isinstance(value, tuple | list):
        return [_canonical_value(item) for item in value]
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise TypeError(f"unsupported approval value: {type(value).__name__}")


def canonical_approval_digest(
    kind: PendingOperationKind,
    payload: object,
    expected_versions: tuple[tuple[str, int], ...],
) -> str:
    """Hash only the semantic fields displayed for approval."""
    document = {
        "expected_versions": _canonical_value(tuple(sorted(expected_versions))),
        "operation_kind": kind.value,
        "payload": _canonical_value(payload),
    }
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def child_operation_id(parent_operation_id: str, index: int, kind: str) -> str:
    """Derive one collision-resistant replay identity for an ordered grouped effect."""
    if not parent_operation_id or index < 0 or not kind:
        raise ValueError("parent operation_id, non-negative index, and kind are required")
    encoded = json.dumps(
        {"index": index, "kind": kind, "parent": parent_operation_id},
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"child-{hashlib.sha256(encoded.encode('utf-8')).hexdigest()}"


class DecisionGrantStore:
    """Hold one-use user decision grants in memory."""

    def __init__(self) -> None:
        self._grants: dict[str, DecisionGrant] = {}
        self._used_user_events: set[tuple[str, str, str]] = set()

    def register(
        self,
        proposal: PendingOperation,
        observation: DecisionObservation,
        grant_id: str,
        created_at: datetime,
    ) -> DecisionGrant:
        if not observation.matched or observation.action is None or not observation.user_event_ref:
            raise ApprovalRejectedError("actual matching user decision required")
        if proposal.state is not CandidateState.AWAITING_DECISION:
            raise ApprovalRejectedError("proposal is not awaiting a decision")
        if grant_id in self._grants:
            raise ApprovalRejectedError("grant id already exists")
        event_key = (proposal.adapter_id, proposal.session_id, observation.user_event_ref)
        if event_key in self._used_user_events:
            raise ApprovalRejectedError("user event already granted a decision")
        action = UserDecisionAction(observation.action.value)
        grant = DecisionGrant(
            grant_id,
            proposal.proposal_id,
            proposal.session_id,
            proposal.adapter_id,
            action,
            proposal.content_digest,
            proposal.expected_versions,
            observation.user_event_ref,
            created_at,
            None,
        )
        self._grants[grant_id] = grant
        self._used_user_events.add(event_key)
        return grant

    def get(self, grant_id: str) -> DecisionGrant | None:
        return self._grants.get(grant_id)

    def consume(self, grant_id: str, consumed_at: datetime) -> DecisionGrant:
        grant = self._grants.get(grant_id)
        if grant is None or grant.consumed_at is not None:
            raise ApprovalRejectedError("unconsumed grant not found")
        consumed = replace(grant, consumed_at=consumed_at)
        self._grants[grant_id] = consumed
        return consumed

    def expire_proposal(self, proposal_id: str) -> None:
        for grant_id, grant in tuple(self._grants.items()):
            if grant.proposal_id == proposal_id and grant.consumed_at is None:
                del self._grants[grant_id]

    def expire_session(self, session_id: str) -> None:
        for grant_id, grant in tuple(self._grants.items()):
            if grant.session_id == session_id and grant.consumed_at is None:
                del self._grants[grant_id]
        self._used_user_events = {item for item in self._used_user_events if item[1] != session_id}


class ApprovalGate:
    """Validate exact proposal, grant, operation, and version binding."""

    def validate(
        self,
        proposal: PendingOperation,
        grant: DecisionGrant,
        operation_id: str,
        current_versions: Mapping[str, int],
        allow_replay: bool,
    ) -> None:
        if proposal.state is not CandidateState.AWAITING_DECISION:
            raise ApprovalRejectedError("proposal is not awaiting a decision")
        if grant.consumed_at is not None:
            raise ApprovalRejectedError("decision grant is already consumed")
        if operation_id != proposal.operation_id:
            raise ApprovalRejectedError("operation_id does not match proposal")
        if (
            grant.proposal_id != proposal.proposal_id
            or grant.session_id != proposal.session_id
            or grant.adapter_id != proposal.adapter_id
        ):
            raise ApprovalRejectedError("decision grant origin does not match proposal")
        if grant.content_digest != proposal.content_digest:
            raise ApprovalRejectedError("decision grant digest does not match proposal")
        if grant.expected_versions != proposal.expected_versions:
            raise ApprovalRejectedError("decision grant versions do not match proposal")
        if grant.action not in {UserDecisionAction.SAVE, UserDecisionAction.CONFIRM_CHANGE}:
            raise ApprovalRejectedError("decision action does not authorize commit")
        digest = canonical_approval_digest(
            proposal.kind, proposal.payload, proposal.expected_versions
        )
        if digest != proposal.content_digest:
            raise ApprovalRejectedError("proposal changed after decision")
        if not allow_replay:
            expected = dict(proposal.expected_versions)
            actual = {key: current_versions.get(key) for key in expected}
            if actual != expected:
                raise StaleVersionError("expected versions are stale")
