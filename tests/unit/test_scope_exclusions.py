#!/usr/bin/env python3
# Purpose: Test src/expertiseos/learning/controls.py literal scope exclusion matching.

from __future__ import annotations

from expertiseos.learning.controls import (
    ContextScope,
    ExclusionKind,
    ScopeExclusion,
    matches_exclusion,
)
from tests.unit.learning_fakes import NOW


def exclusion(kind: ExclusionKind, value: str) -> ScopeExclusion:
    return ScopeExclusion("exclusion-1", kind, value, NOW, "control-operation-1")


def test_source_and_session_match_exactly() -> None:
    context = ContextScope("source-1", "/repo/private/file.py", "session-1")
    assert matches_exclusion(context, (exclusion(ExclusionKind.SOURCE, "source-1"),)) is True
    assert matches_exclusion(context, (exclusion(ExclusionKind.SESSION, "session-1"),)) is True
    assert matches_exclusion(context, (exclusion(ExclusionKind.SOURCE, "source"),)) is False


def test_path_matches_selected_path_and_descendants_not_prefixes() -> None:
    selected = exclusion(ExclusionKind.PATH, "/repo/private")
    assert matches_exclusion(ContextScope(None, "/repo/private", None), (selected,)) is True
    assert matches_exclusion(ContextScope(None, "/repo/private/a.py", None), (selected,)) is True
    prefixed = ContextScope(None, "/repo/private-other/a.py", None)
    assert matches_exclusion(prefixed, (selected,)) is False


def test_empty_or_nonmatching_context_is_not_excluded() -> None:
    selected = exclusion(ExclusionKind.PATH, "/repo/private")
    assert matches_exclusion(ContextScope(None, None, None), (selected,)) is False
    assert matches_exclusion(ContextScope(None, "/repo/public/a.py", None), (selected,)) is False
