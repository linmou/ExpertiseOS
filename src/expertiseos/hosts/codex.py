#!/usr/bin/env python3
# Purpose: Translate evidence-backed Codex hooks into the shared host contract.

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar

from expertiseos.approval.gate import DecisionGrantStore
from expertiseos.domain.candidate_store import CandidateStore
from expertiseos.hosts.contract import (
    DecisionBinding,
    DecisionObservation,
    DecisionRejection,
    EventKind,
    HostCapability,
    HostContractError,
    HostEvent,
)
from expertiseos.learning.controls import (
    ContextScope,
    ControlResolution,
    ScopeExclusion,
    matches_exclusion,
)

T = TypeVar("T")

CODEX_ADAPTER_ID = "codex"
STATIC_EVIDENCE_REF = "specs/001-feasibility-bootstrap/evidence/codex/host-feasibility.md"
SUPPORTED_CODEX_VERSION = "0.146.1"
SUPPORTED_OPERATING_SYSTEM = "macOS 15.1.1 build 24B91"
SUPPORTED_ARCHITECTURE = "arm64"

_HOOK_KINDS: dict[str, EventKind] = {
    "SessionStart": EventKind.SESSION_START,
    "UserPromptSubmit": EventKind.USER_INPUT,
    "PreToolUse": EventKind.ATOMIC_BEGIN,
    "PostToolUse": EventKind.ATOMIC_END,
    "PostToolUseFailure": EventKind.ATOMIC_END,
    "Stop": EventKind.CHECKPOINT,
    "SessionEnd": EventKind.SESSION_END,
}


@dataclass(frozen=True)
class CodexEnvironment:
    version: str
    operating_system: str
    architecture: str
    permission_mode: str

    def __post_init__(self) -> None:
        for value, name in (
            (self.version, "Codex version"),
            (self.operating_system, "operating system"),
            (self.architecture, "architecture"),
            (self.permission_mode, "permission mode"),
        ):
            if not value.strip():
                raise HostContractError(f"{name} is required")


@dataclass(frozen=True)
class CodexRegistrationPlan:
    install_command: tuple[str, ...]
    remove_command: tuple[str, ...]
    preserves_unrelated_configuration: bool
    live_verified: bool


@dataclass(frozen=True)
class OptionalCallResult(Generic[T]):  # noqa: UP046
    value: T | None
    available: bool
    error_type: str | None


def _static_environment_matches(environment: CodexEnvironment) -> bool:
    return (
        environment.version == SUPPORTED_CODEX_VERSION
        and environment.operating_system == SUPPORTED_OPERATING_SYSTEM
        and environment.architecture == SUPPORTED_ARCHITECTURE
    )


def capabilities_for(environment: CodexEnvironment) -> tuple[HostCapability, ...]:
    """Report only the read-only capability profile established by G0."""
    static_match = _static_environment_matches(environment)
    static_limitation = "" if static_match else "environment does not match pinned G0 evidence"
    live_limitation = "live authenticated host fixture not run"
    return (
        HostCapability("can_read", static_match, STATIC_EVIDENCE_REF, static_limitation),
        HostCapability("can_search", static_match, STATIC_EVIDENCE_REF, static_limitation),
        HostCapability("can_validate_user_decisions", False, STATIC_EVIDENCE_REF, live_limitation),
        HostCapability("can_write", False, STATIC_EVIDENCE_REF, live_limitation),
        HostCapability(
            "can_observe_atomic_boundaries", False, STATIC_EVIDENCE_REF, live_limitation
        ),
        HostCapability("can_auto_activate", False, STATIC_EVIDENCE_REF, live_limitation),
    )


def registration_plan(plugin: str, marketplace: str) -> CodexRegistrationPlan:
    """Return reversible public CLI commands without changing user configuration."""
    if not plugin.strip() or not marketplace.strip():
        raise HostContractError("plugin and marketplace are required")
    selector = f"{plugin}@{marketplace}"
    return CodexRegistrationPlan(
        ("codex", "plugin", "add", selector, "--json"),
        ("codex", "plugin", "remove", selector, "--json"),
        False,
        False,
    )


def _required_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HostContractError(f"Codex hook requires {key}")
    return value


def normalize_hook(payload: Mapping[str, object], occurred_at: datetime) -> HostEvent:
    """Normalize documented Codex hook fields without retaining submitted prompt text."""
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise HostContractError("hook timestamp must be timezone-aware")
    hook_name = _required_text(payload, "hook_event_name")
    try:
        kind = _HOOK_KINDS[hook_name]
    except KeyError as error:
        raise HostContractError(f"unsupported Codex hook: {hook_name}") from error
    session_id = _required_text(payload, "session_id")
    reference_key = "turn_id" if kind is EventKind.USER_INPUT else "event_id"
    event_ref = payload.get(reference_key)
    if not isinstance(event_ref, str) or not event_ref.strip():
        if kind in {EventKind.ATOMIC_BEGIN, EventKind.ATOMIC_END}:
            event_ref = _required_text(payload, "tool_use_id")
        else:
            raise HostContractError(f"Codex hook requires {reference_key}")
    if kind is EventKind.USER_INPUT:
        _required_text(payload, "prompt")
    return HostEvent(
        f"{hook_name}:{event_ref}",
        CODEX_ADAPTER_ID,
        session_id,
        kind,
        occurred_at,
        event_ref if kind is EventKind.USER_INPUT else None,
        None,
    )


def should_observe(
    resolution: ControlResolution,
    context: ContextScope,
    exclusions: tuple[ScopeExclusion, ...],
    capabilities: tuple[HostCapability, ...],
) -> bool:
    """Consume C004 policy without recreating its precedence rules."""
    can_write = any(item.name == "can_write" and item.available for item in capabilities)
    return resolution.observe and can_write and not matches_exclusion(context, exclusions)


def should_retrieve(
    resolution: ControlResolution,
    context: ContextScope,
    exclusions: tuple[ScopeExclusion, ...],
    capabilities: tuple[HostCapability, ...],
) -> bool:
    """Allow approved recall only when C004 and the evidence profile permit it."""
    can_search = any(item.name == "can_search" and item.available for item in capabilities)
    return resolution.approved_recall and can_search and not matches_exclusion(context, exclusions)


def try_optional_call(call: Callable[[], T]) -> OptionalCallResult[T]:  # noqa: UP047
    """Contain expertiseOS failures so the caller's host task remains independent."""
    try:
        return OptionalCallResult(call(), True, None)
    except Exception as error:
        return OptionalCallResult(None, False, type(error).__name__)


class CodexAdapter:
    """Read-only Codex adapter for the exact capability profile proven by G0."""

    def __init__(
        self,
        environment: CodexEnvironment,
        session_id: str,
        candidate_store: CandidateStore,
        grant_store: DecisionGrantStore,
    ) -> None:
        if not session_id.strip():
            raise HostContractError("session id is required")
        self._environment = environment
        self._session_id = session_id
        self._candidate_store = candidate_store
        self._grant_store = grant_store
        self._capabilities = capabilities_for(environment)
        self._events: list[HostEvent] = []
        self._seen_event_ids: set[str] = set()
        self._started = False
        self._ended = False
        self._atomic_depth = 0
        self._atomic_state_unknown = False
        self._comparison_due = False
        self._active_binding: DecisionBinding | None = None

    @property
    def adapter_id(self) -> str:
        return CODEX_ADAPTER_ID

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def events(self) -> tuple[HostEvent, ...]:
        return tuple(self._events)

    @property
    def checkpoint_eligible(self) -> bool:
        atomic_proven = any(
            item.name == "can_observe_atomic_boundaries" and item.available
            for item in self._capabilities
        )
        return (
            self._started
            and not self._ended
            and self._atomic_depth == 0
            and not self._atomic_state_unknown
            and atomic_proven
        )

    @property
    def comparison_ready(self) -> bool:
        return self._comparison_due and self.checkpoint_eligible

    @property
    def active_binding(self) -> DecisionBinding | None:
        return self._active_binding

    def capabilities(self) -> tuple[HostCapability, ...]:
        return self._capabilities

    def _accept(self, event: HostEvent, expected_kind: EventKind, require_active: bool) -> None:
        if event.adapter_id != self.adapter_id or event.session_id != self.session_id:
            raise HostContractError("event is outside Codex adapter session")
        if event.kind is not expected_kind:
            raise HostContractError(f"expected {expected_kind}, got {event.kind}")
        if event.event_id in self._seen_event_ids:
            raise HostContractError("duplicate host event")
        if self._ended:
            raise HostContractError("session already ended")
        if require_active and not self._started:
            raise HostContractError("session has not started")

    def _record(self, event: HostEvent) -> None:
        self._seen_event_ids.add(event.event_id)
        self._events.append(event)

    def on_session_start(self, event: HostEvent) -> None:
        self._accept(event, EventKind.SESSION_START, False)
        if self._started:
            raise HostContractError("session already started")
        self._started = True
        self._record(event)

    def on_user_event(self, event: HostEvent) -> None:
        self._accept(event, EventKind.USER_INPUT, True)
        self._record(event)

    def on_unrelated_user_event(self, event: HostEvent) -> None:
        self.on_user_event(event)
        if self._active_binding is not None:
            proposal_id = self._active_binding.proposal_id
            self._candidate_store.expire(proposal_id)
            self._grant_store.expire_proposal(proposal_id)
            self._active_binding = None

    def on_atomic_begin(self, event: HostEvent) -> None:
        self._accept(event, EventKind.ATOMIC_BEGIN, True)
        self._atomic_depth += 1
        self._record(event)

    def on_atomic_end(self, event: HostEvent) -> None:
        self._accept(event, EventKind.ATOMIC_END, True)
        if self._atomic_depth == 0:
            self._atomic_state_unknown = True
            raise HostContractError("atomic operation is not open")
        self._atomic_depth -= 1
        self._record(event)

    def on_checkpoint(self, event: HostEvent) -> None:
        self._accept(event, EventKind.CHECKPOINT, True)
        if self._atomic_depth or self._atomic_state_unknown:
            raise HostContractError("checkpoint is ineligible during unknown or open atomic state")
        self._record(event)

    def on_session_end(self, event: HostEvent) -> None:
        self._accept(event, EventKind.SESSION_END, True)
        self._candidate_store.expire_session(self.session_id)
        self._grant_store.expire_session(self.session_id)
        self._active_binding = None
        self._comparison_due = False
        self._atomic_depth = 0
        self._atomic_state_unknown = False
        self._ended = True
        self._record(event)

    def mark_comparison_due(self) -> None:
        if not self._started or self._ended:
            raise HostContractError("comparison requires an active session")
        self._comparison_due = True

    def consume_comparison_due(self) -> bool:
        if not self.comparison_ready:
            return False
        self._comparison_due = False
        return True

    def display_proposal(self, binding: DecisionBinding) -> None:
        if not self._started or self._ended:
            raise HostContractError("proposal requires an active session")
        if binding.adapter_id != self.adapter_id or binding.session_id != self.session_id:
            raise HostContractError("proposal binding is outside Codex session")
        if (
            self._active_binding is not None
            and self._active_binding.proposal_id != binding.proposal_id
        ):
            raise HostContractError("multiple active proposals require external disambiguation")
        self._active_binding = binding

    def register_decision_if_unambiguous(
        self, event: HostEvent, binding: DecisionBinding
    ) -> DecisionObservation:
        if event.kind is not EventKind.USER_INPUT:
            return DecisionObservation(False, None, None, DecisionRejection.NOT_USER_INPUT)
        if event.adapter_id != self.adapter_id or binding.adapter_id != self.adapter_id:
            return DecisionObservation(False, None, None, DecisionRejection.WRONG_ADAPTER)
        if event.session_id != self.session_id or binding.session_id != self.session_id:
            return DecisionObservation(False, None, None, DecisionRejection.WRONG_SESSION)
        if self._ended:
            return DecisionObservation(False, None, None, DecisionRejection.SESSION_ENDED)
        if event.action is None:
            return DecisionObservation(False, None, None, DecisionRejection.AMBIGUOUS_ACTION)
        if event.action not in binding.allowed_actions:
            return DecisionObservation(False, None, None, DecisionRejection.ACTION_NOT_ALLOWED)
        return DecisionObservation(
            False,
            None,
            None,
            DecisionRejection.MISSING_USER_PROVENANCE,
        )
