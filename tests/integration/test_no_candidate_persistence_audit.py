#!/usr/bin/env python3
# Purpose: Test unique candidate markers are absent from controlled persistent locations.

from __future__ import annotations

from pathlib import Path

from expertiseos.security import ControlledLocation, audit_candidate_absence
from expertiseos.state.sqlite import SQLiteState
from tests.backend_support import FakeBasicMemoryCli, approved, backend
from tests.integration.fixtures.reliability_fixtures import UNIQUE_MARKER


def test_skipped_candidate_marker_is_absent_from_actual_state_files(tmp_path: Path) -> None:
    store = backend(tmp_path, FakeBasicMemoryCli())
    store.create_approved(
        approved("approved only", None, ("fact",), ("domain",), ("host:1",)), "create-1"
    )
    state_path = tmp_path / "state.sqlite"
    state = SQLiteState(state_path)
    state.close()
    report = audit_candidate_absence(
        "skip-fixture",
        UNIQUE_MARKER,
        (
            ControlledLocation("backend", tmp_path / "backend-state.json"),
            ControlledLocation("state", state_path),
        ),
        ("host conversation history",),
    )
    assert report.passed
    assert len(report.locations) == 2
