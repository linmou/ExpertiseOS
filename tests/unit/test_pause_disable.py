#!/usr/bin/env python3
# Purpose: Test src/expertiseos/learning/controls.py pause/disable precedence and permissions.

from __future__ import annotations

import dataclasses
from datetime import timedelta
from decimal import Decimal

import pytest

from expertiseos.learning.controls import (
    ControlReason,
    PeriodProgress,
    default_daily_settings,
    resolve_controls,
)
from tests.unit.learning_fakes import NOW


def progress(reflections: int = 0) -> PeriodProgress:
    return PeriodProgress("2026-09-14", reflections, Decimal("0"), (), ())


@pytest.mark.parametrize(
    ("disabled", "paused", "rest", "reflections", "reason", "permissions"),
    [
        (True, True, True, 1, ControlReason.DISABLED, (False, False, False, False)),
        (False, True, True, 1, ControlReason.PAUSED, (False, False, False, True)),
        (False, False, True, 1, ControlReason.FATIGUE_REST, (False, False, False, True)),
        (False, False, False, 1, ControlReason.TARGET_SATISFIED, (True, True, False, True)),
        (False, False, False, 0, ControlReason.ACTIVE, (True, True, True, True)),
    ],
)
def test_control_precedence_and_permissions(
    disabled: bool,
    paused: bool,
    rest: bool,
    reflections: int,
    reason: ControlReason,
    permissions: tuple[bool, bool, bool, bool],
) -> None:
    settings = default_daily_settings("America/New_York", 1)
    settings = dataclasses.replace(
        settings,
        enabled=not disabled,
        learning_paused=paused,
        fatigue_rest_until=NOW + timedelta(hours=1) if rest else None,
    )
    result = resolve_controls(settings, progress(reflections), NOW)
    assert result.reason is reason
    assert (
        result.observe,
        result.prompt_collection,
        result.proactive_exercises,
        result.approved_recall,
    ) == permissions


def test_expired_pause_and_rest_do_not_remain_active() -> None:
    settings = dataclasses.replace(
        default_daily_settings("UTC", 1),
        learning_paused=True,
        pause_until=NOW - timedelta(seconds=1),
        fatigue_rest_until=NOW - timedelta(seconds=1),
    )
    assert resolve_controls(settings, progress(), NOW).reason is ControlReason.ACTIVE


def test_one_off_explanation_does_not_mutate_or_resume_pause() -> None:
    settings = dataclasses.replace(default_daily_settings("UTC", 1), learning_paused=True)
    before = settings
    assert resolve_controls(settings, progress(), NOW).approved_recall is True
    assert settings == before
