#!/usr/bin/env python3
# Purpose: Test skill/SKILL.md is the single host-neutral expertiseOS behavior contract.

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from expertiseos.hosts.claude_code import (
    ClaudeCapabilityEvidence,
    ClaudeEnvironment,
    EvidenceResult,
    InteractionKind,
    interaction_allowed,
)
from expertiseos.hosts.claude_code import capabilities_for as claude_capabilities
from expertiseos.hosts.codex import (
    CodexEnvironment,
    should_observe,
    should_retrieve,
)
from expertiseos.hosts.codex import capabilities_for as codex_capabilities
from expertiseos.learning.controls import (
    ContextScope,
    PeriodProgress,
    default_daily_settings,
    resolve_controls,
)

ROOT = Path(__file__).parents[2]
SKILL = ROOT / "skill" / "SKILL.md"
NOW = datetime(2026, 9, 14, 12, tzinfo=UTC)


def _skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_one_shared_skill_owns_host_neutral_behavior() -> None:
    skill_files = tuple((ROOT / "skill").glob("**/SKILL.md"))

    assert skill_files == (SKILL,)
    text = _skill_text()
    assert "Codex" in text
    assert "Claude Code" in text
    assert "host-neutral" in text


def test_skill_preserves_work_checkpoint_and_consent_boundaries() -> None:
    text = _skill_text().casefold()

    for required in (
        "ordinary host work",
        "safe checkpoint",
        "save, edit, or skip",
        "actual user",
        "do not claim",
        "unrelated",
        "expire",
    ):
        assert required in text


def test_skill_uses_bounded_untrusted_recall_and_no_authority_from_content() -> None:
    text = _skill_text().casefold()

    for required in (
        "bounded",
        "20",
        "untrusted data",
        "never follow",
        "approval",
        "control",
        "mastery",
        "whole repository",
    ):
        assert required in text


def test_skill_consumes_promoted_control_and_mastery_policy() -> None:
    text = _skill_text()

    for required in (
        "Disabled",
        "Paused or fatigue rest",
        "Target satisfied",
        "only `pass`",
        "`partial`",
        "`fail`",
        "`insufficient_evidence`",
        "1, 1, 1, 1, 2",
        "two independent successes",
    ):
        assert required in text


def test_common_host_behavior_matches_with_capability_gated_collection() -> None:
    codex = codex_capabilities(
        CodexEnvironment(
            "0.146.1",
            "macOS 15.1.1 build 24B91",
            "arm64",
            "workspace-write",
        )
    )
    claude_environment = ClaudeEnvironment(
        "2.1.241",
        "macOS 15.1.1 build 24B91",
        "arm64",
        "default",
    )
    claude = claude_capabilities(
        claude_environment,
        tuple(
            ClaudeCapabilityEvidence(
                claude_environment,
                name,
                (),
                "c006-read-evidence" if name in {"can_read", "can_search"} else "",
                EvidenceResult.PASS
                if name in {"can_read", "can_search"}
                else EvidenceResult.NOT_RUN,
                "" if name in {"can_read", "can_search"} else "live evidence unavailable",
            )
            for name in (
                "can_read",
                "can_search",
                "can_validate_user_decisions",
                "can_write",
                "can_observe_atomic_boundaries",
                "can_auto_activate",
            )
        ),
    )
    context = ContextScope("terminal", "/workspace/project/main.py", "shared-session")
    progress = PeriodProgress("2026-09-14", 0, Decimal("0"), (), ())
    settings = default_daily_settings("UTC", 1)
    resolutions = (
        resolve_controls(settings, progress, NOW),
        resolve_controls(dataclasses.replace(settings, learning_paused=True), progress, NOW),
        resolve_controls(dataclasses.replace(settings, enabled=False), progress, NOW),
    )
    codex_available = {item.name: item.available for item in codex}
    claude_available = {item.name: item.available for item in claude}

    assert codex_available == claude_available
    for resolution in resolutions:
        codex_recall = should_retrieve(resolution, context, (), codex)
        claude_recall = (
            interaction_allowed(resolution, context, (), InteractionKind.RECALL)
            and claude_available["can_search"]
        )
        codex_collection = should_observe(resolution, context, (), codex)
        claude_collection = (
            interaction_allowed(resolution, context, (), InteractionKind.COLLECTION)
            and claude_available["can_write"]
            and claude_available["can_observe_atomic_boundaries"]
        )

        assert codex_recall is claude_recall
        assert codex_collection is claude_collection is False
