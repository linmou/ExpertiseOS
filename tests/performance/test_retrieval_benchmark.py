#!/usr/bin/env python3
# Purpose: Benchmark BasicMemoryBackend bounded retrieval over 10,000 canonical fixture notes.

from __future__ import annotations

import json
import os
import platform
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path

from expertiseos.backends.basic_memory import BasicMemoryBackend
from expertiseos.knowledge.backend import KnowledgeRecord, KnowledgeStatus, SearchQuery
from tests.backend_support import FakeBasicMemoryCli, approved, backend


def test_warm_retrieval_p95_for_ten_thousand_objects(tmp_path: Path) -> None:
    cli = FakeBasicMemoryCli()
    timestamp = datetime(2026, 9, 14, tzinfo=UTC)
    records: dict[str, dict[str, object]] = {}
    for index in range(10_000):
        value = approved(
            f"benchmark item {index} target-{index % 100}",
            None,
            ("fact",),
            ("domain",),
            (f"fixture:{index}",),
        )
        knowledge_id = f"benchmark-{index:05d}"
        record = KnowledgeRecord(
            knowledge_id,
            1,
            value.content,
            value.content_digest,
            value.categories,
            value.subjects,
            value.applicability_scope,
            value.evidential_status,
            value.source_refs,
            value.contribution_origin,
            KnowledgeStatus.ACTIVE,
            (),
            timestamp,
            timestamp,
        )
        identifier = f"expertiseos/{knowledge_id}-v1"
        cli.notes[identifier] = BasicMemoryBackend._note(record, f"fixture-{index}")
        records[knowledge_id] = {"current": 1, "versions": {"1": identifier}}
    state_path = tmp_path / "backend-state.json"
    state_path.write_text(
        json.dumps({"schema": 1, "records": records, "operations": {}, "tokens": {}}),
        encoding="utf-8",
    )
    store = backend(tmp_path, cli)
    query = SearchQuery("target-42", 20, None, (), (), ())
    store.search(query)
    samples: list[float] = []
    for _ in range(30):
        started = time.perf_counter()
        results = store.search(query)
        samples.append((time.perf_counter() - started) * 1000)
        assert len(results) <= 20
    p95_ms = statistics.quantiles(samples, n=100, method="inclusive")[94]
    metadata = {
        "backend": "BasicMemoryBackend with deterministic public-CLI fixture",
        "basic_memory_version": "0.23.2",
        "corpus_size": 10_000,
        "cpu_count": os.cpu_count(),
        "hardware_architecture": platform.machine(),
        "index_mode": "local indexed",
        "os": platform.platform(),
        "python": platform.python_version(),
        "sample_count": len(samples),
        "warmup_count": 1,
        "warm_retrieval_p95_ms": p95_ms,
    }
    evidence = Path(
        os.environ.get("EXPERTISEOS_BENCHMARK_EVIDENCE", str(tmp_path / "retrieval-benchmark.json"))
    )
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    assert p95_ms < 1_000
