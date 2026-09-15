#!/usr/bin/env python3
# Purpose: Test src/expertiseos/__main__.py through the installed module health entrypoint.

from __future__ import annotations

import json
import subprocess
import sys


def test_bootstrap_health_entrypoint() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "expertiseos", "--health"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert json.loads(completed.stdout) == {
        "service": "expertiseos",
        "status": "bootstrap-ready",
    }
    assert completed.stderr == ""
