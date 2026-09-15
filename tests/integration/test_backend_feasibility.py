#!/usr/bin/env python3
# Purpose: Test Basic Memory 0.23.2 public CLI create/read/search/relation/delete/rebuild behavior.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.external]


def basic_memory_binary() -> Path:
    binary = Path(sys.executable).with_name("basic-memory")
    if not binary.exists():
        pytest.skip("basic-memory optional G0 dependency is not installed")
    return binary


def isolated_environment(tmp_path: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "BASIC_MEMORY_CONFIG_DIR": str(tmp_path / "config"),
            "BASIC_MEMORY_HOME": str(tmp_path / "knowledge"),
            "BASIC_MEMORY_AUTO_UPDATE": "false",
            "BASIC_MEMORY_SEMANTIC_SEARCH_ENABLED": "false",
        }
    )
    return environment


def run_bm(binary: Path, environment: dict[str, str], *arguments: str) -> str:
    result = subprocess.run(
        (str(binary), *arguments),
        check=True,
        capture_output=True,
        text=True,
        env=environment,
        timeout=30,
    )
    return result.stdout


def fixture() -> dict[str, Any]:
    path = Path(__file__).parents[1] / "fixtures" / "approved_knowledge.json"
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def configure_project(binary: Path, environment: dict[str, str], tmp_path: Path) -> None:
    run_bm(
        binary,
        environment,
        "project",
        "add",
        "g0",
        str(tmp_path / "project"),
        "--local",
        "--default",
    )


def write_note(binary: Path, environment: dict[str, str], note: dict[str, str]) -> dict[str, Any]:
    output = run_bm(
        binary,
        environment,
        "tool",
        "write-note",
        "--title",
        note["title"],
        "--folder",
        note["folder"],
        "--content",
        note["content"],
        "--project",
        "g0",
        "--local",
    )
    return cast(dict[str, Any], json.loads(output))


def test_public_cli_round_trip_metadata_relations_search_delete_and_rebuild(
    tmp_path: Path,
) -> None:
    binary = basic_memory_binary()
    environment = isolated_environment(tmp_path)
    values = fixture()
    configure_project(binary, environment, tmp_path)

    target = write_note(binary, environment, values["target"])
    source = write_note(binary, environment, values["source"])
    assert target["action"] == "created"
    assert source["action"] == "created"

    read_output = run_bm(
        binary,
        environment,
        "tool",
        "read-note",
        "tests/g0-approved-source",
        "--project",
        "g0",
        "--json",
        "--local",
    )
    read_value = json.loads(read_output)
    assert "Retry only when" in read_value["content"]
    assert "supports [[G0 Approved Target]]" in read_value["content"]
    assert read_value["frontmatter"]["tags"] == ["retry", "safety"]

    search_output = run_bm(
        binary,
        environment,
        "tool",
        "search-notes",
        values["query"],
        "--project",
        "g0",
        "--json",
        "--page-size",
        str(values["page_size"]),
        "--local",
    )
    results = json.loads(search_output)
    assert results["page_size"] == 1
    assert results["total"] >= 1
    assert results["results"][0]["external_id"]

    run_bm(binary, environment, "reindex", "--search", "--project", "g0")
    deleted = json.loads(
        run_bm(
            binary,
            environment,
            "tool",
            "delete-note",
            "tests/g0-approved-source",
            "--project",
            "g0",
            "--local",
        )
    )
    assert deleted["deleted"] is True
    missing = json.loads(
        run_bm(
            binary,
            environment,
            "tool",
            "read-note",
            "tests/g0-approved-source",
            "--project",
            "g0",
            "--json",
            "--local",
        )
    )
    assert missing["content"] is None
