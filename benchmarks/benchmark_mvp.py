#!/usr/bin/env python3
# Purpose: Benchmark MVP lifecycle, warm retrieval, and approved-write latency deterministically.

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from expertiseos.backends.basic_memory import BasicMemoryBackend  # noqa: E402
from expertiseos.knowledge.backend import (  # noqa: E402
    KnowledgeRecord,
    KnowledgeStatus,
    SearchQuery,
)
from expertiseos.reliability import OperationKind, OperationRecord, OperationStatus  # noqa: E402
from tests.backend_support import FakeBasicMemoryCli, approved, backend  # noqa: E402


def _percentiles(samples: list[float], threshold_ms: float) -> dict[str, Any]:
    quantiles = statistics.quantiles(samples, n=100, method="inclusive")
    p95 = quantiles[94]
    return {
        "samples_ms": samples,
        "sample_count": len(samples),
        "p50_ms": statistics.median(samples),
        "p95_ms": p95,
        "p99_ms": quantiles[98],
        "threshold_ms": threshold_ms,
        "passed": p95 < threshold_ms,
    }


def _measure(action: Callable[[], Any], count: int) -> list[float]:
    samples: list[float] = []
    for _ in range(count):
        started = time.perf_counter()
        action()
        samples.append((time.perf_counter() - started) * 1_000)
    return samples


def _git_commit() -> str:
    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _basic_memory_version() -> str:
    try:
        return importlib.metadata.version("basic-memory")
    except importlib.metadata.PackageNotFoundError:
        return "0.23.2-declared-fixture"


def run(corpus_size: int, seed: int) -> dict[str, Any]:
    randomizer = random.Random(seed)
    timestamp = datetime(2026, 9, 14, tzinfo=UTC)
    with TemporaryDirectory(prefix="expertiseos-benchmark-") as directory:
        root = Path(directory)
        cli = FakeBasicMemoryCli()
        records: dict[str, dict[str, object]] = {}
        print(f"building deterministic corpus: {corpus_size} objects", file=sys.stderr)
        for index in range(corpus_size):
            bucket = randomizer.randrange(100)
            value = approved(
                f"benchmark item {index} target-{bucket}",
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
        (root / "backend-state.json").write_text(
            json.dumps({"schema": 1, "records": records, "operations": {}, "tokens": {}}),
            encoding="utf-8",
        )
        store = backend(root, cli)

        print("warming local retrieval", file=sys.stderr)
        query = SearchQuery("target-42", 20, None, (), (), ())
        store.search(query)
        retrieval = _measure(lambda: store.search(query), 30)

        operation_index = 0

        def bookkeeping() -> OperationRecord:
            nonlocal operation_index
            operation_index += 1
            return OperationRecord(
                f"operation-{operation_index}",
                OperationKind.INDEX_REBUILD,
                ((f"benchmark-{operation_index % corpus_size:05d}", 1),),
                OperationStatus.PENDING,
            )

        print("measuring lifecycle bookkeeping", file=sys.stderr)
        lifecycle = _measure(bookkeeping, 100)

        write_index = 0

        def approved_write() -> KnowledgeRecord:
            nonlocal write_index
            write_index += 1
            return store.create_approved(
                approved(
                    f"approved benchmark write {write_index}",
                    None,
                    ("fact",),
                    ("domain",),
                    (f"benchmark-write:{write_index}",),
                ),
                f"benchmark-write-{write_index}",
            )

        print("measuring approved-write acknowledgement", file=sys.stderr)
        writes = _measure(approved_write, 20)

    command = (
        f"python benchmarks/benchmark_mvp.py --corpus-size {corpus_size} "
        f"--seed {seed} --output <path>"
    )
    return {
        "schema_version": 1,
        "command": command,
        "commit": _git_commit(),
        "environment": {
            "hardware_architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "os": platform.platform(),
            "python": platform.python_version(),
            "basic_memory": _basic_memory_version(),
            "backend": "BasicMemoryBackend deterministic public-CLI fixture",
            "index": "local indexed keyword fixture; semantic disabled",
        },
        "corpus": {
            "size": corpus_size,
            "seed": seed,
            "shape": "small approved knowledge records across 100 deterministic query buckets",
        },
        "warmup_count": 1,
        "operations": {
            "lifecycle_bookkeeping": _percentiles(lifecycle, 200.0),
            "warm_local_retrieval": _percentiles(retrieval, 1_000.0),
            "approved_write_acknowledgement": _percentiles(writes, 1_000.0),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-size", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.corpus_size < 100:
        parser.error("--corpus-size must be at least 100")
    result = run(arguments.corpus_size, arguments.seed)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    passed = all(bool(value["passed"]) for value in result["operations"].values())
    print(f"wrote benchmark evidence: {arguments.output}", file=sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
