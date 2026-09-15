#!/usr/bin/env python3
# Purpose: Test src/expertiseos/learning/controls.py periods, fatigue, and target distinctions.

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from expertiseos.domain.errors import DomainValidationError
from expertiseos.learning.controls import (
    ControlReason,
    PeriodProgress,
    TargetPeriod,
    default_daily_settings,
    default_weekly_settings,
    fatigue_transition,
    period_key,
    resolve_controls,
)
from tests.unit.learning_fakes import NOW


def progress(reflections: int, effort: str = "0") -> PeriodProgress:
    return PeriodProgress("2026-09-14", reflections, Decimal(effort), (), ())


def test_target_satisfied_and_fatigue_are_distinct() -> None:
    settings = default_daily_settings("UTC", 1)
    target = resolve_controls(settings, progress(1), NOW)
    fatigue = fatigue_transition(settings, NOW, None)
    rested_settings = dataclasses.replace(settings, fatigue_rest_until=fatigue.rest_until)
    rested = resolve_controls(rested_settings, progress(0), NOW)
    assert target.reason is ControlReason.TARGET_SATISFIED
    assert target.prompt_collection is True
    assert rested.reason is ControlReason.FATIGUE_REST
    assert rested.prompt_collection is False
    assert fatigue.expire_unresolved_candidates is True
    assert fatigue.mark_target_satisfied is False


def test_fatigue_uses_default_or_positive_user_duration() -> None:
    settings = default_daily_settings("UTC", 1)
    assert fatigue_transition(settings, NOW, None).rest_until == NOW + timedelta(minutes=60)
    assert fatigue_transition(settings, NOW, 15).rest_until == NOW + timedelta(minutes=15)
    with pytest.raises(DomainValidationError, match="positive integer"):
        fatigue_transition(settings, NOW, 0)


def test_daily_and_weekly_period_keys_use_configured_timezone() -> None:
    instant = datetime(2026, 9, 14, 2, 30, tzinfo=UTC)
    daily = default_daily_settings("America/New_York", 1)
    weekly = default_weekly_settings("America/New_York", 1)
    assert weekly.target_period is TargetPeriod.WEEKLY
    assert weekly.reflection_target == 3
    assert period_key(daily, instant) == "2026-09-13"
    assert period_key(weekly, instant).startswith("2026-W37")


def test_new_period_does_not_cancel_pause() -> None:
    settings = dataclasses.replace(default_daily_settings("UTC", 1), learning_paused=True)
    next_day = NOW + timedelta(days=1)
    next_progress = PeriodProgress(period_key(settings, next_day), 0, Decimal("0"), (), ())
    assert resolve_controls(settings, next_progress, next_day).reason is ControlReason.PAUSED
