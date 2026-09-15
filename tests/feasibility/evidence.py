#!/usr/bin/env python3
# Purpose: Validate and write complete, reproducible G0 capability evidence records.

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    component: str
    version_or_commit: str
    operating_system: str
    architecture: str
    capability: str
    command_or_manual_steps: tuple[str, ...]
    input_fixture: str
    expected_output: str
    observed_output_or_log: str
    exit_status: int | None
    captured_at_utc: str
    result: str
    limitation: str

    def validate(self) -> None:
        required = (
            self.evidence_id,
            self.component,
            self.version_or_commit,
            self.operating_system,
            self.architecture,
            self.capability,
            self.command_or_manual_steps,
            self.input_fixture,
            self.expected_output,
            self.observed_output_or_log,
            self.captured_at_utc,
        )
        if not all(required):
            raise ValueError("evidence metadata is incomplete")
        if self.result not in {"pass", "limited", "fail", "not_run"}:
            raise ValueError("invalid evidence result")
        if self.result == "pass" and self.exit_status != 0:
            raise ValueError("passed command evidence requires zero exit status")
        if self.result in {"limited", "fail", "not_run"} and not self.limitation:
            raise ValueError("non-passing evidence requires a capability limitation")


def write_evidence(record: EvidenceRecord, path: Path) -> None:
    record.validate()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(record), indent=2, sort_keys=True) + "\n", encoding="utf-8")
