#!/usr/bin/env python3
# Purpose: Test src/expertiseos/hosts/codex.py reversible non-mutating onboarding plans.

import pytest

from expertiseos.hosts.codex import registration_plan
from expertiseos.hosts.contract import HostContractError


def test_registration_plan_uses_public_reversible_plugin_commands() -> None:
    plan = registration_plan("expertiseos", "local")
    assert plan.install_command == (
        "codex",
        "plugin",
        "add",
        "expertiseos@local",
        "--json",
    )
    assert plan.remove_command == (
        "codex",
        "plugin",
        "remove",
        "expertiseos@local",
        "--json",
    )
    assert plan.preserves_unrelated_configuration is False
    assert plan.live_verified is False


@pytest.mark.parametrize("plugin, marketplace", [("", "local"), ("expertiseos", " ")])
def test_registration_plan_rejects_missing_selector_parts(plugin: str, marketplace: str) -> None:
    with pytest.raises(HostContractError, match="plugin and marketplace"):
        registration_plan(plugin, marketplace)
