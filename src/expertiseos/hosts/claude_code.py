#!/usr/bin/env python3
# Purpose: Translate evidence-backed Claude Code hooks into the shared host contract.

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol, TypeVar

from expertiseos.domain.models import CommitResult, CommitStatus
from expertiseos.hosts.contract import (
    DecisionAction,
    DecisionBinding,
    DecisionObservation,
    DecisionRejection,
    EventKind,
    HostAdapter,
    HostCapability,
    HostContractError,
    HostEvent,
)
from expertiseos.knowledge.backend import RetrievalResponse, SearchQuery
from expertiseos.learning.controls import (
    ContextScope,
    ControlResolution,
    ScopeExclusion,
    matches_exclusion,
)

ADAPTER_ID = "claude-code"
CAPABILITY_NAMES = (
    "can_read",
    "can_search",
    "can_validate_user_decisions",
    "can_write",
    "can_observe_atomic_boundaries",
    "can_auto_activate",
)


class EvidenceResult(StrEnum):
    PASS = "pass"
    LIMITED = "limited"
    FAILED = "failed"
    NOT_RUN = "not_run"


class RawOrigin(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    MODEL = "model"
    LIFECYCLE = "lifecycle"


class InteractionKind(StrEnum):
    OBSERVE = "observe"
    COLLECTION = "collection"
    EXERCISE = "exercise"
    RECALL = "recall"


@dataclass(frozen=True)
class ClaudeEnvironment:
    version: str
    operating_system: str
    architecture: str
    permission_mode: str

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.version,
                self.operating_system,
                self.architecture,
                self.permission_mode,
            )
        ):
            raise HostContractError("Claude environment fields are required")


@dataclass(frozen=True)
class ClaudeCapabilityEvidence:
    environment: ClaudeEnvironment
    capability_name: str
    event_names: tuple[str, ...]
    evidence_ref: str
    result: EvidenceResult
    limitation: str

    def __post_init__(self) -> None:
        if self.capability_name not in CAPABILITY_NAMES:
            raise HostContractError("unknown Claude capability")
        if self.result is EvidenceResult.PASS and not self.evidence_ref:
            raise HostContractError("passed capability requires evidence")
        if self.result is not EvidenceResult.PASS and not self.limitation:
            raise HostContractError("unavailable capability requires a limitation")


@dataclass(frozen=True)
class ClaudeRawEvent:
    event_id: str
    event_name: str
    session_id: str
    occurred_at: datetime
    origin: RawOrigin
    prompt: str | None
    user_input_ref: str | None

    def __post_init__(self) -> None:
        if not self.event_id or not self.event_name or not self.session_id:
            raise HostContractError("Claude event identities are required")
        if self.origin is RawOrigin.USER and not self.user_input_ref:
            raise HostContractError("Claude user event requires public hook provenance")
        if self.origin is not RawOrigin.USER and self.user_input_ref is not None:
            raise HostContractError("non-user Claude event cannot carry user provenance")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise HostContractError("Claude event time must be timezone-aware")


class ClaudeService(Protocol):
    def search(self, query: SearchQuery) -> RetrievalResponse: ...

    def decline(self, proposal_id: str, fingerprint: str | None) -> object: ...

    def expire_session(self, session_id: str) -> tuple[str, ...]: ...

    def expire_unrelated_decisions(
        self, session_id: str, active_proposal_id: str | None
    ) -> tuple[str, ...]: ...


T = TypeVar("T")


def capabilities_for(
    environment: ClaudeEnvironment,
    evidence: tuple[ClaudeCapabilityEvidence, ...],
) -> tuple[HostCapability, ...]:
    """Report only capabilities passed for the exact running environment."""
    matching = tuple(item for item in evidence if item.environment == environment)
    names = tuple(item.capability_name for item in matching)
    if len(names) != len(set(names)):
        raise HostContractError("duplicate Claude capability evidence")
    selected = {item.capability_name: item for item in matching}
    decision_passed = (
        selected.get("can_validate_user_decisions") is not None
        and selected["can_validate_user_decisions"].result is EvidenceResult.PASS
    )
    capabilities: list[HostCapability] = []
    for name in CAPABILITY_NAMES:
        item = selected.get(name)
        available = item is not None and item.result is EvidenceResult.PASS
        if name == "can_write":
            available = available and decision_passed
        evidence_ref = "" if item is None else item.evidence_ref
        limitation = "no evidence for the running environment" if item is None else item.limitation
        if name == "can_write" and not decision_passed:
            limitation = "live actual-user decision validation has not passed"
        capabilities.append(HostCapability(name, available, evidence_ref, limitation))
    return tuple(capabilities)


def plugin_commands(plugin_source: str, plugin_name: str) -> tuple[tuple[str, ...], ...]:
    """Return public Claude CLI commands without editing host configuration directly."""
    if not plugin_source.strip() or not plugin_name.strip():
        raise HostContractError("plugin source and name are required")
    return (
        ("claude", "plugin", "install", plugin_source),
        ("claude", "plugin", "uninstall", plugin_name),
    )


def parse_explicit_action(prompt: str | None) -> DecisionAction | None:
    """Recognize only complete standalone decision controls."""
    if prompt is None:
        return None
    normalized = " ".join(prompt.strip().lower().split())
    actions = {
        "save": DecisionAction.SAVE,
        "skip": DecisionAction.SKIP,
        "cancel": DecisionAction.SKIP,
        "confirm change": DecisionAction.CONFIRM_CHANGE,
    }
    if normalized.startswith("edit: ") and normalized.removeprefix("edit: ").strip():
        return DecisionAction.EDIT
    if normalized.startswith("save: ") and normalized.removeprefix("save: ").strip():
        return DecisionAction.SAVE
    return actions.get(normalized)


def explicit_edit_content(prompt: str | None) -> str | None:
    """Return final edit content only for the explicit `Edit: content` form."""
    if prompt is None or not prompt.strip().lower().startswith("edit:"):
        return None
    content = prompt.strip()[len("edit:") :].strip()
    return content or None


def direct_save_content(prompt: str | None, immediate_reference: str | None) -> str | None:
    """Resolve only exact direct-save forms without semantic interpretation."""
    if prompt is None:
        return None
    stripped = prompt.strip()
    lowered = stripped.lower()
    if lowered.startswith("save: "):
        content = stripped[len("save: ") :].strip()
        return content or None
    if lowered in {"save this", "save it"} and immediate_reference is not None:
        content = immediate_reference.strip()
        return content or None
    return None


def is_saved_result(result: object) -> bool:
    """Map only a complete C002 commit to a host-facing Saved result."""
    return isinstance(result, CommitResult) and result.status is CommitStatus.COMMITTED


def interaction_allowed(
    resolution: ControlResolution,
    context: ContextScope,
    exclusions: tuple[ScopeExclusion, ...],
    interaction: InteractionKind,
) -> bool:
    """Consume C004's resolved permissions without recreating precedence."""
    if matches_exclusion(context, exclusions):
        return False
    permissions = {
        InteractionKind.OBSERVE: resolution.observe,
        InteractionKind.COLLECTION: resolution.prompt_collection,
        InteractionKind.EXERCISE: resolution.proactive_exercises,
        InteractionKind.RECALL: resolution.approved_recall,
    }
    return permissions[interaction]


class ClaudeCodeAdapter(HostAdapter):
    def __init__(
        self,
        session_id: str,
        environment: ClaudeEnvironment,
        evidence: tuple[ClaudeCapabilityEvidence, ...],
        service: ClaudeService,
    ) -> None:
        if not session_id:
            raise HostContractError("session id is required")
        self._session_id = session_id
        self._environment = environment
        self._capabilities = capabilities_for(environment, evidence)
        self._service = service
        self._events: list[HostEvent] = []
        self._observed_user_events: set[str] = set()
        self._atomic_depth = 0
        self._comparison_due = False
        self._active_binding: DecisionBinding | None = None
        self._started = False
        self._ended = False
        self._last_memory_error: str | None = None

    @property
    def adapter_id(self) -> str:
        return ADAPTER_ID

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def events(self) -> tuple[HostEvent, ...]:
        return tuple(self._events)

    @property
    def atomic_depth(self) -> int:
        return self._atomic_depth

    @property
    def comparison_due(self) -> bool:
        return self._comparison_due

    @property
    def last_memory_error(self) -> str | None:
        return self._last_memory_error

    @property
    def write_capable(self) -> bool:
        return self.capability_available("can_write")

    @property
    def checkpoint_capable(self) -> bool:
        return self.capability_available("can_observe_atomic_boundaries")

    def capability_available(self, name: str) -> bool:
        if name not in CAPABILITY_NAMES:
            raise HostContractError("unknown Claude capability")
        return any(item.name == name and item.available for item in self._capabilities)

    def capabilities(self) -> tuple[HostCapability, ...]:
        return self._capabilities

    def set_active_binding(self, binding: DecisionBinding) -> None:
        if binding.adapter_id != self.adapter_id or binding.session_id != self.session_id:
            raise HostContractError("decision binding is outside adapter session")
        self._active_binding = binding

    def clear_active_binding(self) -> None:
        self._active_binding = None

    def checkpoint_eligible(
        self,
        resolution: ControlResolution,
        context: ContextScope,
        exclusions: tuple[ScopeExclusion, ...],
        interaction: InteractionKind,
    ) -> bool:
        return (
            self._started
            and not self._ended
            and self._atomic_depth == 0
            and self.checkpoint_capable
            and interaction_allowed(resolution, context, exclusions, interaction)
        )

    def normalize(self, raw: ClaudeRawEvent) -> HostEvent:
        if raw.session_id != self.session_id:
            raise HostContractError("Claude event is outside adapter session")
        event_kind = {
            "SessionStart": EventKind.SESSION_START,
            "UserPromptSubmit": EventKind.USER_INPUT,
            "PreToolUse": EventKind.ATOMIC_BEGIN,
            "PostToolUse": EventKind.ATOMIC_END,
            "PostToolUseFailure": EventKind.ATOMIC_END,
            "Stop": EventKind.CHECKPOINT,
            "SessionEnd": EventKind.SESSION_END,
        }.get(raw.event_name)
        if event_kind is None:
            raise HostContractError("unsupported Claude event")
        if event_kind is EventKind.USER_INPUT and raw.origin is not RawOrigin.USER:
            raise HostContractError("UserPromptSubmit must have actual-user origin")
        action = parse_explicit_action(raw.prompt) if event_kind is EventKind.USER_INPUT else None
        user_ref = raw.user_input_ref if event_kind is EventKind.USER_INPUT else None
        return HostEvent(
            raw.event_id,
            self.adapter_id,
            raw.session_id,
            event_kind,
            raw.occurred_at,
            user_ref,
            action,
        )

    def handle_raw_event(self, raw: ClaudeRawEvent) -> HostEvent:
        event = self.normalize(raw)
        handlers: Mapping[EventKind, Callable[[HostEvent], None]] = {
            EventKind.SESSION_START: self.on_session_start,
            EventKind.USER_INPUT: self.on_user_event,
            EventKind.ATOMIC_BEGIN: self.on_atomic_begin,
            EventKind.ATOMIC_END: self.on_atomic_end,
            EventKind.CHECKPOINT: self.on_checkpoint,
            EventKind.SESSION_END: self.on_session_end,
        }
        handlers[event.kind](event)
        return event

    def _accept(self, event: HostEvent, expected: EventKind) -> None:
        if event.adapter_id != self.adapter_id or event.session_id != self.session_id:
            raise HostContractError("event is outside adapter session")
        if event.kind is not expected:
            raise HostContractError(f"expected {expected}, got {event.kind}")
        if self._ended:
            raise HostContractError("session already ended")

    def _accept_active(self, event: HostEvent, expected: EventKind) -> None:
        self._accept(event, expected)
        if not self._started:
            raise HostContractError("session has not started")

    def on_session_start(self, event: HostEvent) -> None:
        self._accept(event, EventKind.SESSION_START)
        if self._started:
            raise HostContractError("session already started")
        self._started = True
        self._events.append(event)

    def on_user_event(self, event: HostEvent) -> None:
        self._accept_active(event, EventKind.USER_INPUT)
        self._events.append(event)

    def on_atomic_begin(self, event: HostEvent) -> None:
        self._accept_active(event, EventKind.ATOMIC_BEGIN)
        self._atomic_depth += 1
        self._comparison_due = True
        self._events.append(event)

    def on_atomic_end(self, event: HostEvent) -> None:
        self._accept_active(event, EventKind.ATOMIC_END)
        if self._atomic_depth == 0:
            raise HostContractError("atomic operation is not open")
        self._atomic_depth -= 1
        self._events.append(event)

    def on_checkpoint(self, event: HostEvent) -> None:
        self._accept_active(event, EventKind.CHECKPOINT)
        if self._atomic_depth:
            raise HostContractError("checkpoint is ineligible during atomic operation")
        self._comparison_due = False
        self._events.append(event)

    def on_session_end(self, event: HostEvent) -> None:
        self._accept_active(event, EventKind.SESSION_END)
        self._optional_call(lambda: self._service.expire_session(self.session_id))
        self._active_binding = None
        self._observed_user_events.clear()
        self._atomic_depth = 0
        self._comparison_due = False
        self._ended = True
        self._events.append(event)

    def register_decision_if_unambiguous(
        self, event: HostEvent, binding: DecisionBinding
    ) -> DecisionObservation:
        rejection = self._decision_rejection(event, binding)
        if rejection is not DecisionRejection.NONE:
            if (
                event.kind is EventKind.USER_INPUT
                and rejection is DecisionRejection.AMBIGUOUS_ACTION
            ):
                self._expire_unrelated()
            return DecisionObservation(False, None, None, rejection)
        assert event.action is not None
        assert event.user_input_ref is not None
        self._observed_user_events.add(event.event_id)
        if event.action is DecisionAction.SKIP:
            self._optional_call(lambda: self._service.decline(binding.proposal_id, None))
            self._active_binding = None
        return DecisionObservation(True, event.action, event.user_input_ref, DecisionRejection.NONE)

    def _decision_rejection(self, event: HostEvent, binding: DecisionBinding) -> DecisionRejection:
        if self._ended:
            return DecisionRejection.SESSION_ENDED
        if event.kind is not EventKind.USER_INPUT:
            return DecisionRejection.NOT_USER_INPUT
        if not event.user_input_ref:
            return DecisionRejection.MISSING_USER_PROVENANCE
        if event.adapter_id != self.adapter_id or binding.adapter_id != self.adapter_id:
            return DecisionRejection.WRONG_ADAPTER
        if event.session_id != self.session_id or binding.session_id != self.session_id:
            return DecisionRejection.WRONG_SESSION
        if event.event_id in self._observed_user_events:
            return DecisionRejection.ALREADY_OBSERVED
        if self._active_binding != binding:
            return DecisionRejection.ACTION_NOT_ALLOWED
        if event.action is None:
            return DecisionRejection.AMBIGUOUS_ACTION
        if event.action not in binding.allowed_actions:
            return DecisionRejection.ACTION_NOT_ALLOWED
        if event.action in {DecisionAction.SAVE, DecisionAction.CONFIRM_CHANGE} and not (
            self.write_capable
        ):
            return DecisionRejection.ACTION_NOT_ALLOWED
        return DecisionRejection.NONE

    def _expire_unrelated(self) -> None:
        self._optional_call(lambda: self._service.expire_unrelated_decisions(self.session_id, None))
        self._active_binding = None

    def search(
        self,
        query: SearchQuery,
        resolution: ControlResolution,
        context: ContextScope,
        exclusions: tuple[ScopeExclusion, ...],
    ) -> RetrievalResponse | None:
        if not self.capability_available("can_search") or not interaction_allowed(
            resolution, context, exclusions, InteractionKind.RECALL
        ):
            return None
        response = self._optional_call(lambda: self._service.search(query))
        if response is None:
            return None
        if not isinstance(response, RetrievalResponse) or len(response.results) > query.limit:
            self._last_memory_error = "MalformedRetrievalResponse"
            return None
        return response

    def _optional_call(self, operation: Callable[[], T]) -> T | None:
        try:
            result = operation()
        except Exception as error:
            self._last_memory_error = error.__class__.__name__
            return None
        self._last_memory_error = None
        return result
