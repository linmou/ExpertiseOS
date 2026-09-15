#!/usr/bin/env python3
# Purpose: Test src/expertiseos/hosts/codex.py does not overclaim unavailable live evidence.

from expertiseos.hosts.codex import CodexEnvironment, capabilities_for, registration_plan


def test_current_g0_profile_stays_read_only_until_live_fixture_passes() -> None:
    environment = CodexEnvironment(
        "0.146.1",
        "macOS 15.1.1 build 24B91",
        "arm64",
        "workspace-write",
    )
    capabilities = {item.name: item for item in capabilities_for(environment)}
    setup = registration_plan("expertiseos", "local")

    assert capabilities["can_read"].available
    assert capabilities["can_search"].available
    assert not capabilities["can_validate_user_decisions"].available
    assert not capabilities["can_write"].available
    assert not capabilities["can_observe_atomic_boundaries"].available
    assert not capabilities["can_auto_activate"].available
    assert not setup.preserves_unrelated_configuration
    assert not setup.live_verified
