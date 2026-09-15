#!/usr/bin/env python3
# Purpose: Resolve learning controls and validate bounded reflection/deferred behavior.

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from pathlib import PurePath
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from expertiseos.domain.errors import DomainValidationError
from expertiseos.learning.evidence import AdvancementThresholds, ApprovedObjectFact

ZERO_EFFORT = Decimal("0")
SIMPLE_EFFORT = Decimal("0.25")
BRIEF_EFFORT = Decimal("1.0")
SUBSTANTIAL_EFFORT = Decimal("2.0")


def _require_text(value: str, name: str) -> None:
    if not value or not value.strip():
        raise DomainValidationError(f"{name} is required")


def _require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainValidationError(f"{name} must be timezone-aware")


class TargetPeriod(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"


class ControlReason(StrEnum):
    DISABLED = "disabled"
    PAUSED = "paused"
    FATIGUE_REST = "fatigue_rest"
    TARGET_SATISFIED = "target_satisfied"
    ACTIVE = "active"


class ExclusionKind(StrEnum):
    SOURCE = "source"
    PATH = "path"
    SESSION = "session"


class DeferredStatus(StrEnum):
    PENDING = "pending"
    REMOVED = "removed"


@dataclass(frozen=True)
class ControlSettings:
    enabled: bool
    learning_paused: bool
    pause_until: datetime | None
    target_period: TargetPeriod
    reflection_target: int
    effort_limit: Decimal
    rest_interval_minutes: int
    fatigue_rest_until: datetime | None
    timezone_id: str
    advancement_thresholds: AdvancementThresholds
    version: int

    def __post_init__(self) -> None:
        for value, name in (
            (self.pause_until, "pause end"),
            (self.fatigue_rest_until, "fatigue rest end"),
        ):
            if value is not None:
                _require_aware(value, name)
        if type(self.reflection_target) is not int or self.reflection_target < 1:
            raise DomainValidationError("reflection target must be a positive integer")
        if self.effort_limit <= ZERO_EFFORT:
            raise DomainValidationError("effort limit must be positive")
        if type(self.rest_interval_minutes) is not int or self.rest_interval_minutes < 1:
            raise DomainValidationError("rest interval must be a positive integer")
        if self.version < 1:
            raise DomainValidationError("control version must be positive")
        _zone(self.timezone_id)


@dataclass(frozen=True)
class PeriodProgress:
    period_key: str
    reflection_count: int
    effort_units: Decimal
    reflection_event_ids: tuple[str, ...]
    effort_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.period_key, "period key")
        if self.reflection_count < 0 or self.effort_units < ZERO_EFFORT:
            raise DomainValidationError("period progress cannot be negative")
        if len(self.reflection_event_ids) != len(set(self.reflection_event_ids)):
            raise DomainValidationError("duplicate reflection event id")
        if len(self.effort_event_ids) != len(set(self.effort_event_ids)):
            raise DomainValidationError("duplicate effort event id")


@dataclass(frozen=True)
class ControlResolution:
    reason: ControlReason
    observe: bool
    prompt_collection: bool
    proactive_exercises: bool
    approved_recall: bool
    expires_at: datetime | None


@dataclass(frozen=True)
class FatigueTransition:
    rest_until: datetime
    expire_unresolved_candidates: bool
    mark_target_satisfied: bool


@dataclass(frozen=True)
class ResponseFacts:
    event_id: str
    simple_decision: bool
    brief_response: bool
    substantial_reflection: bool
    ordinary_task_activity: bool
    model_only_output: bool

    def __post_init__(self) -> None:
        _require_text(self.event_id, "response event id")


@dataclass(frozen=True)
class ReflectionActivityFacts:
    event_id: str
    meaningful_user_contribution: bool
    develops_reusable_knowledge: bool
    connected_to_approved: bool
    saved_with_approval: bool
    linked_output_count: int

    def __post_init__(self) -> None:
        _require_text(self.event_id, "reflection event id")
        if self.linked_output_count < 1:
            raise DomainValidationError("reflection must have at least one linked output")


@dataclass(frozen=True)
class ContextScope:
    source_id: str | None
    path: str | None
    session_id: str | None

    def __post_init__(self) -> None:
        for value, name in (
            (self.source_id, "source id"),
            (self.path, "path"),
            (self.session_id, "session id"),
        ):
            if value is not None and not value.strip():
                raise DomainValidationError(f"{name} cannot be blank")


@dataclass(frozen=True)
class ScopeExclusion:
    id: str
    kind: ExclusionKind
    value: str
    created_at: datetime
    approval_receipt_id: str

    def __post_init__(self) -> None:
        _require_text(self.id, "exclusion id")
        _require_text(self.value, "exclusion value")
        _require_text(self.approval_receipt_id, "approval receipt id")
        _require_aware(self.created_at, "exclusion creation time")


@dataclass(frozen=True)
class ApprovedKnowledgeRef:
    knowledge_id: str
    version: int

    def __post_init__(self) -> None:
        _require_text(self.knowledge_id, "knowledge id")
        if self.version < 1:
            raise DomainValidationError("knowledge version must be positive")


@dataclass(frozen=True)
class DeferredActivity:
    id: str
    knowledge_refs: tuple[ApprovedKnowledgeRef, ...]
    activity_type: str
    created_at: datetime
    status: DeferredStatus
    approval_receipt_id: str

    def __post_init__(self) -> None:
        _require_text(self.id, "deferred activity id")
        _require_text(self.activity_type, "activity type")
        _require_text(self.approval_receipt_id, "approval receipt id")
        _require_aware(self.created_at, "deferred activity creation time")
        if not self.knowledge_refs:
            raise DomainValidationError("deferred activity requires approved knowledge")


@dataclass(frozen=True)
class ControlInspection:
    settings: ControlSettings
    resolution: ControlResolution
    progress: PeriodProgress
    exclusions: tuple[ScopeExclusion, ...]
    deferred_activities: tuple[DeferredActivity, ...]
    truncated: bool


def _zone(timezone_id: str) -> ZoneInfo:
    _require_text(timezone_id, "timezone id")
    try:
        return ZoneInfo(timezone_id)
    except ZoneInfoNotFoundError as error:
        raise DomainValidationError("unknown timezone id") from error


def default_daily_settings(timezone_id: str, version: int) -> ControlSettings:
    """Instantiate every MVP default explicitly."""
    return ControlSettings(
        True,
        False,
        None,
        TargetPeriod.DAILY,
        1,
        Decimal("6"),
        60,
        None,
        timezone_id,
        AdvancementThresholds(1, 1, 1, 1, 2),
        version,
    )


def default_weekly_settings(timezone_id: str, version: int) -> ControlSettings:
    """Instantiate the weekly MVP preset with every field explicit."""
    daily = default_daily_settings(timezone_id, version)
    return replace(daily, target_period=TargetPeriod.WEEKLY, reflection_target=3)


def period_key(settings: ControlSettings, now: datetime) -> str:
    _require_aware(now, "current time")
    local = now.astimezone(_zone(settings.timezone_id))
    if settings.target_period is TargetPeriod.DAILY:
        return local.date().isoformat()
    year, week, _ = local.isocalendar()
    return f"{year}-W{week:02d}"


def _active_until(enabled: bool, until: datetime | None, now: datetime) -> bool:
    return enabled and (until is None or now < until)


def resolve_controls(
    settings: ControlSettings, progress: PeriodProgress, now: datetime
) -> ControlResolution:
    """Resolve the global control reason without mutating settings or progress."""
    _require_aware(now, "current time")
    if not settings.enabled:
        return ControlResolution(ControlReason.DISABLED, False, False, False, False, None)
    if _active_until(settings.learning_paused, settings.pause_until, now):
        return ControlResolution(
            ControlReason.PAUSED, False, False, False, True, settings.pause_until
        )
    if settings.fatigue_rest_until is not None and now < settings.fatigue_rest_until:
        return ControlResolution(
            ControlReason.FATIGUE_REST,
            False,
            False,
            False,
            True,
            settings.fatigue_rest_until,
        )
    if progress.reflection_count >= settings.reflection_target:
        return ControlResolution(ControlReason.TARGET_SATISFIED, True, True, False, True, None)
    return ControlResolution(ControlReason.ACTIVE, True, True, True, True, None)


def fatigue_transition(
    settings: ControlSettings,
    now: datetime,
    duration_minutes: int | None,
) -> FatigueTransition:
    _require_aware(now, "current time")
    duration = settings.rest_interval_minutes if duration_minutes is None else duration_minutes
    if type(duration) is not int or duration < 1:
        raise DomainValidationError("fatigue duration must be a positive integer")
    return FatigueTransition(now + timedelta(minutes=duration), True, False)


def classify_effort(facts: ResponseFacts) -> Decimal:
    if facts.ordinary_task_activity or facts.model_only_output:
        return ZERO_EFFORT
    if facts.substantial_reflection:
        return SUBSTANTIAL_EFFORT
    if facts.brief_response:
        return BRIEF_EFFORT
    if facts.simple_decision:
        return SIMPLE_EFFORT
    return ZERO_EFFORT


def record_effort_once(progress: PeriodProgress, facts: ResponseFacts) -> PeriodProgress:
    if facts.event_id in progress.effort_event_ids:
        return progress
    units = classify_effort(facts)
    if units == ZERO_EFFORT:
        return progress
    return replace(
        progress,
        effort_units=progress.effort_units + units,
        effort_event_ids=progress.effort_event_ids + (facts.event_id,),
    )


def effort_limit_reached(limit: Decimal, progress: PeriodProgress) -> bool:
    if limit <= ZERO_EFFORT:
        raise DomainValidationError("effort limit must be positive")
    return progress.effort_units >= limit


def qualifies_reflection(facts: ReflectionActivityFacts) -> bool:
    return (
        facts.meaningful_user_contribution
        and facts.develops_reusable_knowledge
        and facts.connected_to_approved
        and facts.saved_with_approval
    )


def record_reflection_once(
    progress: PeriodProgress, facts: ReflectionActivityFacts
) -> PeriodProgress:
    if not qualifies_reflection(facts) or facts.event_id in progress.reflection_event_ids:
        return progress
    return replace(
        progress,
        reflection_count=progress.reflection_count + 1,
        reflection_event_ids=progress.reflection_event_ids + (facts.event_id,),
    )


def _normalized_path(value: str) -> PurePath:
    return PurePath(os.path.normpath(value))


def matches_exclusion(context: ContextScope, exclusions: tuple[ScopeExclusion, ...]) -> bool:
    for item in exclusions:
        if item.kind is ExclusionKind.SOURCE and context.source_id == item.value:
            return True
        if item.kind is ExclusionKind.SESSION and context.session_id == item.value:
            return True
        if item.kind is ExclusionKind.PATH and context.path is not None:
            context_path = _normalized_path(context.path)
            excluded_path = _normalized_path(item.value)
            if context_path == excluded_path or excluded_path in context_path.parents:
                return True
    return False


def validate_deferred_activity(
    activity: DeferredActivity,
    approved_objects: tuple[ApprovedObjectFact, ...],
) -> DeferredActivity:
    refs = tuple((item.knowledge_id, item.version) for item in activity.knowledge_refs)
    if len(refs) != len(set(refs)):
        raise DomainValidationError("duplicate deferred knowledge reference")
    approved = {(item.knowledge_id, item.knowledge_version) for item in approved_objects}
    if any(item not in approved for item in refs):
        raise DomainValidationError("deferred activity references unavailable approved knowledge")
    return activity


def remove_deferred(activity: DeferredActivity, approval_receipt_id: str) -> DeferredActivity:
    """Return the explicit approved removal intent without touching durable state."""
    _require_text(approval_receipt_id, "approval receipt id")
    return replace(
        activity,
        status=DeferredStatus.REMOVED,
        approval_receipt_id=approval_receipt_id,
    )


def can_offer_deferred(
    activity: DeferredActivity,
    resolution: ControlResolution,
    foreground_session: bool,
    session_started_at: datetime,
) -> bool:
    _require_aware(session_started_at, "session start time")
    return (
        activity.status is DeferredStatus.PENDING
        and resolution.reason is ControlReason.ACTIVE
        and foreground_session
        and session_started_at > activity.created_at
    )


def inspect_controls(
    settings: ControlSettings,
    progress: PeriodProgress,
    exclusions: tuple[ScopeExclusion, ...],
    deferred_activities: tuple[DeferredActivity, ...],
    now: datetime,
    limit: int,
) -> ControlInspection:
    if not 1 <= limit <= 20:
        raise DomainValidationError("inspection limit must be between 1 and 20")
    return ControlInspection(
        settings,
        resolve_controls(settings, progress, now),
        progress,
        exclusions[:limit],
        deferred_activities[:limit],
        len(exclusions) > limit or len(deferred_activities) > limit,
    )
