#!/usr/bin/env python3
# Purpose: Test src/expertiseos/learning/controls.py qualifying reflection counting.

from __future__ import annotations

from decimal import Decimal

import pytest

from expertiseos.learning.controls import (
    PeriodProgress,
    ReflectionActivityFacts,
    qualifies_reflection,
    record_reflection_once,
)


def activity() -> ReflectionActivityFacts:
    return ReflectionActivityFacts("reflection-1", True, True, True, True, 3)


def test_qualifying_activity_counts_once_regardless_of_linked_outputs_or_retry() -> None:
    progress = PeriodProgress("2026-09-14", 0, Decimal("0"), (), ())
    first = record_reflection_once(progress, activity())
    second = record_reflection_once(first, activity())
    assert first == second
    assert first.reflection_count == 1


@pytest.mark.parametrize(
    "item",
    [
        ReflectionActivityFacts("reflection-1", False, True, True, True, 3),
        ReflectionActivityFacts("reflection-1", True, False, True, True, 3),
        ReflectionActivityFacts("reflection-1", True, True, False, True, 3),
        ReflectionActivityFacts("reflection-1", True, True, True, False, 3),
    ],
)
def test_each_qualification_condition_is_required(item: ReflectionActivityFacts) -> None:
    assert qualifies_reflection(item) is False


def test_raw_log_paraphrase_relabel_and_assistant_only_facts_do_not_qualify() -> None:
    for item in (
        ReflectionActivityFacts("raw", False, False, False, False, 1),
        ReflectionActivityFacts("paraphrase", True, False, True, True, 1),
        ReflectionActivityFacts("relabel", False, True, True, True, 1),
        ReflectionActivityFacts("assistant", False, True, True, True, 4),
    ):
        assert qualifies_reflection(item) is False
