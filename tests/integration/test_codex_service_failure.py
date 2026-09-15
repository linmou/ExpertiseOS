#!/usr/bin/env python3
# Purpose: Test src/expertiseos/hosts/codex.py contains optional service failures.

import pytest

from expertiseos.hosts.codex import try_optional_call

pytestmark = pytest.mark.integration


class ServiceUnavailableError(RuntimeError):
    pass


def test_service_failure_does_not_replace_completed_host_result() -> None:
    host_result = {"task": "complete", "artifact": "unchanged"}

    def unavailable() -> object:
        raise ServiceUnavailableError("local service unavailable")

    side_result = try_optional_call(unavailable)

    assert host_result == {"task": "complete", "artifact": "unchanged"}
    assert side_result.value is None
    assert side_result.available is False
    assert side_result.error_type == "ServiceUnavailableError"


def test_successful_optional_read_returns_value_without_saved_claim() -> None:
    result = try_optional_call(lambda: {"results": (), "degraded": True})
    assert result.available
    assert result.value == {"results": (), "degraded": True}
    assert result.error_type is None
