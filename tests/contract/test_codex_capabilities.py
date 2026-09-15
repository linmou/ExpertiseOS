#!/usr/bin/env python3
# Purpose: Test src/expertiseos/hosts/codex.py evidence-backed capability reporting.

import pytest

from expertiseos.hosts.codex import CodexEnvironment, capabilities_for
from expertiseos.hosts.contract import HostContractError


def capability_map(environment: CodexEnvironment) -> dict[str, bool]:
    return {item.name: item.available for item in capabilities_for(environment)}


def test_exact_g0_environment_is_read_only() -> None:
    values = capability_map(
        CodexEnvironment("0.146.1", "macOS 15.1.1 build 24B91", "arm64", "workspace-write")
    )
    assert values == {
        "can_read": True,
        "can_search": True,
        "can_validate_user_decisions": False,
        "can_write": False,
        "can_observe_atomic_boundaries": False,
        "can_auto_activate": False,
    }


@pytest.mark.parametrize(
    "environment",
    [
        CodexEnvironment("0.146.2", "macOS 15.1.1 build 24B91", "arm64", "workspace-write"),
        CodexEnvironment("0.146.1", "macOS 15.2", "arm64", "workspace-write"),
        CodexEnvironment("0.146.1", "macOS 15.1.1 build 24B91", "x86_64", "workspace-write"),
    ],
)
def test_unmatched_environment_has_no_capabilities(environment: CodexEnvironment) -> None:
    assert not any(capability_map(environment).values())


def test_permission_mode_is_reported_but_cannot_promote_writes() -> None:
    restricted = capability_map(
        CodexEnvironment("0.146.1", "macOS 15.1.1 build 24B91", "arm64", "read-only")
    )
    assert restricted["can_read"]
    assert not restricted["can_write"]


def test_environment_fields_are_required() -> None:
    with pytest.raises(HostContractError, match="permission mode"):
        CodexEnvironment("0.146.1", "macOS 15.1.1 build 24B91", "arm64", "")
