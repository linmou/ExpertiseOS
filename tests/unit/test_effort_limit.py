#!/usr/bin/env python3
# Purpose: Test src/expertiseos/learning/controls.py effort classification and idempotency.

from __future__ import annotations

from decimal import Decimal

from expertiseos.learning.controls import (
    PeriodProgress,
    ResponseFacts,
    classify_effort,
    effort_limit_reached,
    record_effort_once,
)


def facts(
    identifier: str,
    *,
    simple: bool = False,
    brief: bool = False,
    substantial: bool = False,
    ordinary: bool = False,
    model_only: bool = False,
) -> ResponseFacts:
    return ResponseFacts(identifier, simple, brief, substantial, ordinary, model_only)


def test_effort_uses_highest_applicable_category() -> None:
    assert classify_effort(facts("e0")) == Decimal("0")
    assert classify_effort(facts("e1", simple=True)) == Decimal("0.25")
    assert classify_effort(facts("e2", brief=True)) == Decimal("1.0")
    assert classify_effort(facts("e3", simple=True, brief=True, substantial=True)) == Decimal("2.0")


def test_ordinary_task_and_model_only_output_count_zero() -> None:
    assert classify_effort(facts("e1", substantial=True, ordinary=True)) == Decimal("0")
    assert classify_effort(facts("e2", substantial=True, model_only=True)) == Decimal("0")


def test_duplicate_event_is_counted_once_and_limit_is_exact() -> None:
    progress = PeriodProgress("2026-09-14", 0, Decimal("5"), (), ())
    event = facts("e1", brief=True)
    first = record_effort_once(progress, event)
    second = record_effort_once(first, event)
    assert first == second
    assert first.effort_units == Decimal("6.0")
    assert effort_limit_reached(Decimal("6"), first) is True
