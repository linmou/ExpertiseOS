#!/usr/bin/env python3
# Purpose: Test C008 fixtures consume actual promoted C002-C004 producer implementations.

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from expertiseos.backends.basic_memory import BasicMemoryBackend
from expertiseos.knowledge.service import KnowledgeService
from expertiseos.state.sqlite import SQLiteState
from tests.e2e.conftest import ProductGraph
from tests.e2e.evidence import AcceptanceEvidence, write_evidence


def test_product_graph_preserves_actual_promoted_handoffs(product_graph: ProductGraph) -> None:
    assert type(product_graph.knowledge) is KnowledgeService
    assert type(product_graph.backend) is BasicMemoryBackend
    assert type(product_graph.state) is SQLiteState
    assert product_graph.knowledge._backend is product_graph.backend
    assert product_graph.knowledge._receipts is product_graph.state


def test_evidence_records_tested_sha_without_future_promotion_sha(tmp_path: Path) -> None:
    stamp = datetime(2026, 9, 14, tzinfo=UTC).isoformat()
    evidence = AcceptanceEvidence(
        1,
        "AT-04",
        "d754a5a56596cce559688e4066042235bd3ea35e",
        ("python", "-m", "pytest", "tests/e2e"),
        0,
        stamp,
        stamp,
        (("python", "3.12"),),
        ("scenario-a-v1",),
        ("C002->C003",),
        ("approved-record",),
        "pass",
        "artifacts/c008/at-04.log",
    )

    destination = write_evidence(evidence, tmp_path / "at-04.json")
    payload = destination.read_text(encoding="utf-8")

    assert '"tested_sha"' in payload
    assert "promotion_sha" not in payload
    assert "candidate_content" not in payload
