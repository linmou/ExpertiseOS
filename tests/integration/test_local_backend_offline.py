#!/usr/bin/env python3
# Purpose: Test Basic Memory local keyword read/search with outbound network denied after setup.

from __future__ import annotations

import json
import platform
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.integration.test_backend_feasibility import (
    basic_memory_binary,
    configure_project,
    fixture,
    isolated_environment,
    write_note,
)

pytestmark = [pytest.mark.integration, pytest.mark.external]


def offline_command(binary: Path, *arguments: str) -> tuple[str, ...]:
    sandbox = shutil.which("sandbox-exec")
    if platform.system() != "Darwin" or sandbox is None:
        pytest.skip("outbound-denial fixture currently uses the supported macOS sandbox")
    profile = "(version 1) (allow default) (deny network*)"
    return (sandbox, "-p", profile, str(binary), *arguments)


def test_keyword_read_and_search_work_with_network_denied(tmp_path: Path) -> None:
    binary = basic_memory_binary()
    environment = isolated_environment(tmp_path)
    values = fixture()
    configure_project(binary, environment, tmp_path)
    write_note(binary, environment, values["source"])

    read = subprocess.run(
        offline_command(
            binary,
            "tool",
            "read-note",
            "tests/g0-approved-source",
            "--project",
            "g0",
            "--json",
            "--local",
        ),
        check=True,
        capture_output=True,
        text=True,
        env=environment,
        timeout=30,
    )
    assert "Retry only when" in json.loads(read.stdout)["content"]

    search = subprocess.run(
        offline_command(
            binary,
            "tool",
            "search-notes",
            values["query"],
            "--project",
            "g0",
            "--json",
            "--page-size",
            "1",
            "--local",
        ),
        check=True,
        capture_output=True,
        text=True,
        env=environment,
        timeout=30,
    )
    payload = json.loads(search.stdout)
    assert payload["total"] >= 1
    assert payload["results"][0]["content"]
