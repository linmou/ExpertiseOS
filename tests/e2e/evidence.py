#!/usr/bin/env python3
# Purpose: Record safe reproducible C008 acceptance-run metadata without candidate content.

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class AcceptanceEvidence:
    schema_version: int
    at_id: str
    tested_sha: str
    command: tuple[str, ...]
    exit_code: int
    started_at: str
    finished_at: str
    environment: tuple[tuple[str, str], ...]
    fixture_versions: tuple[str, ...]
    producer_consumer_edges: tuple[str, ...]
    edge_artifacts: tuple[str, ...]
    result: str
    output_path: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported evidence schema")
        if not self.at_id.startswith("AT-") or not self.tested_sha:
            raise ValueError("acceptance identity and tested SHA are required")
        if self.result not in {"pass", "fail", "not_applicable"}:
            raise ValueError("invalid acceptance result")
        if not self.command or self.exit_code < 0 or not self.output_path:
            raise ValueError("command, exit code, and output path are required")


def write_evidence(evidence: AcceptanceEvidence, destination: Path) -> Path:
    """Write only the fixed metadata schema; no free-form candidate payload field exists."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(asdict(evidence), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def deterministic_verdict(
    quality_by_at: Mapping[str, str],
    evidence: tuple[AcceptanceEvidence, ...],
) -> str:
    """Return a deterministic verdict without accepting model-quality offsets."""
    by_id = {item.at_id: item for item in evidence}
    if set(by_id) != set(quality_by_at):
        raise ValueError("acceptance evidence is incomplete")
    if any(item.result == "fail" for item in by_id.values()):
        return "fail"
    return "pass"
