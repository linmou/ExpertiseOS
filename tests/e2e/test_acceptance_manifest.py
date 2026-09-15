#!/usr/bin/env python3
# Purpose: Verify complete AT-01 through AT-16 metadata and deterministic verdict inputs.

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import cast

import pytest

from tests.e2e.evidence import AcceptanceEvidence, deterministic_verdict

MANIFEST = Path(__file__).parents[2] / "examples/reference_scenarios/acceptance_manifest.json"


def _cases() -> list[dict[str, object]]:
    document = cast(dict[str, object], json.loads(MANIFEST.read_text(encoding="utf-8")))
    assert document["schema_version"] == 1
    return cast(list[dict[str, object]], document["cases"])


def _evidence(at_id: str, result: str) -> AcceptanceEvidence:
    return AcceptanceEvidence(
        1,
        at_id,
        "a09bea40478e2c770469f8282ff9e343a6a9da9a",
        ("python", "-m", "pytest", "tests/e2e"),
        0 if result != "fail" else 1,
        "2026-09-14T12:00:00+00:00",
        "2026-09-14T12:01:00+00:00",
        (("network_mode", "blocked"),),
        ("c008-acceptance-corpus-v1",),
        ("C008->integration",),
        (f"test:{at_id}",),
        result,
        f"evidence/{at_id}.json",
    )


def test_manifest_maps_exactly_at01_through_at16_with_required_case_fields() -> None:
    cases = _cases()
    expected_ids = {f"AT-{index:02d}" for index in range(1, 17)}
    required = {
        "at_id",
        "applicable_environments",
        "fixture_ids",
        "producer_consumer_edges",
        "assertions",
        "quality_class",
    }

    assert {str(item["at_id"]) for item in cases} == expected_ids
    assert len(cases) == len(expected_ids)
    assert {field.name for field in dataclasses.fields(AcceptanceEvidence)} == {
        "schema_version",
        "at_id",
        "tested_sha",
        "command",
        "exit_code",
        "started_at",
        "finished_at",
        "environment",
        "fixture_versions",
        "producer_consumer_edges",
        "edge_artifacts",
        "result",
        "output_path",
    }
    for case in cases:
        assert set(case) == required
        assert all(case[field] for field in required)


def test_deterministic_failure_cannot_be_offset_by_model_behavior_score() -> None:
    quality = {str(item["at_id"]): str(item["quality_class"]) for item in _cases()}
    evidence = tuple(_evidence(at_id, "fail" if at_id == "AT-06" else "pass") for at_id in quality)
    model_behavior_score = 1.0

    assert model_behavior_score == 1.0
    assert deterministic_verdict(quality, evidence) == "fail"


def test_incomplete_evidence_cannot_produce_a_verdict() -> None:
    quality = {str(item["at_id"]): str(item["quality_class"]) for item in _cases()}

    with pytest.raises(ValueError, match="incomplete"):
        deterministic_verdict(quality, (_evidence("AT-01", "pass"),))
