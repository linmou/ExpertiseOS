#!/usr/bin/env python3
# Purpose: Test tests/feasibility/evidence.py completeness and false-support safeguards.

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.feasibility.evidence import EvidenceRecord, write_evidence


def record(result: str, exit_status: int | None, limitation: str) -> EvidenceRecord:
    return EvidenceRecord(
        "evidence-1",
        "component",
        "1.0.0",
        "macOS 15.1.1",
        "arm64",
        "capability",
        ("command --version",),
        "fixture",
        "expected",
        "observed",
        exit_status,
        "2026-09-14T00:00:00Z",
        result,
        limitation,
    )


def test_pass_requires_zero_exit_status() -> None:
    with pytest.raises(ValueError, match="zero"):
        record("pass", 1, "").validate()


def test_non_pass_requires_limitation() -> None:
    with pytest.raises(ValueError, match="limitation"):
        record("not_run", None, "").validate()


def test_write_evidence_preserves_metadata(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    write_evidence(record("pass", 0, ""), path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["result"] == "pass"
    assert payload["command_or_manual_steps"] == ["command --version"]
