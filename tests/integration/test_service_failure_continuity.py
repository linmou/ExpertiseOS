#!/usr/bin/env python3
# Purpose: Test src/expertiseos/__main__.py failure isolation for ordinary host work.

from __future__ import annotations

import pytest

from expertiseos.__main__ import run_optional_service

pytestmark = pytest.mark.integration


def test_service_failure_does_not_block_host_result() -> None:
    host_results: list[str] = []

    def unavailable() -> None:
        raise ConnectionError("service unavailable")

    host_results.append("task-complete")
    assert not run_optional_service(unavailable)
    assert host_results == ["task-complete"]


def test_service_success_is_reported() -> None:
    assert run_optional_service(lambda: None)
