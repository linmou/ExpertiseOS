#!/usr/bin/env python3
# Purpose: Verify integrated host activation, scope, novelty/conflict, and checkpoint acceptance.

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

from expertiseos.hosts.claude_code import (
    ClaudeCapabilityEvidence,
    ClaudeEnvironment,
    EvidenceResult,
    InteractionKind,
    interaction_allowed,
    plugin_commands,
)
from expertiseos.hosts.claude_code import capabilities_for as claude_capabilities
from expertiseos.hosts.codex import (
    CodexEnvironment,
    registration_plan,
    should_observe,
    should_retrieve,
)
from expertiseos.hosts.codex import capabilities_for as codex_capabilities
from expertiseos.knowledge.backend import RelationshipInput, RetrievalResponse, SearchQuery
from expertiseos.learning.controls import (
    ContextScope,
    ExclusionKind,
    PeriodProgress,
    ScopeExclusion,
    default_daily_settings,
    resolve_controls,
)
from expertiseos.service import ExpertiseOSService, ToolStatus
from tests.backend_support import approved
from tests.consent_support import NOW
from tests.e2e.conftest import ProductGraph

CORPUS = Path(__file__).parents[2] / "examples/reference_scenarios/acceptance_corpus.json"


def test_at01_both_hosts_have_guided_reversible_activation_and_truthful_capabilities() -> None:
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
                "read-evidence" if name in {"can_read", "can_search"} else "",
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
    codex_setup = registration_plan("expertiseos", "local")
    claude_setup = plugin_commands("./expertiseos", "expertiseos")

    assert {item.name: item.available for item in codex} == {
        item.name: item.available for item in claude
    }
    assert codex_setup.install_command[:3] == ("codex", "plugin", "add")
    assert codex_setup.remove_command[:3] == ("codex", "plugin", "remove")
    assert claude_setup[0][:3] == ("claude", "plugin", "install")
    assert claude_setup[1][:3] == ("claude", "plugin", "uninstall")
    assert all(item.available is False for item in codex if item.name.startswith("can_auto"))
    assert all("api_key" not in field for field in CodexEnvironment.__dataclass_fields__)
    assert all("api_key" not in field for field in ClaudeEnvironment.__dataclass_fields__)


def test_at01_scope_exclusion_applies_to_both_host_decisions() -> None:
    context = ContextScope("terminal", "/workspace/private/note.md", "session-shared")
    exclusion = ScopeExclusion(
        "exclude-private",
        ExclusionKind.PATH,
        "/workspace/private",
        datetime(2026, 9, 14, tzinfo=UTC),
        "control-operation",
    )
    active = resolve_controls(
        default_daily_settings("UTC", 1),
        PeriodProgress("2026-09-14", 0, Decimal("0"), (), ()),
        NOW,
    )
    capabilities = codex_capabilities(
        CodexEnvironment(
            "0.146.1",
            "macOS 15.1.1 build 24B91",
            "arm64",
            "workspace-write",
        )
    )

    assert should_retrieve(active, context, (exclusion,), capabilities) is False
    assert should_observe(active, context, (exclusion,), capabilities) is False
    assert interaction_allowed(active, context, (exclusion,), InteractionKind.RECALL) is False
    assert interaction_allowed(active, context, (exclusion,), InteractionKind.COLLECTION) is False


def test_at02_conflict_is_retrieved_as_untrusted_visible_state(
    product_graph: ProductGraph,
) -> None:
    first = product_graph.backend.create_approved(
        approved("retry three times", None, ("fact",), ("domain",), ("source:first",)),
        "host-conflict-first",
    )
    second = product_graph.backend.create_approved(
        approved("retry five times", None, ("fact",), ("domain",), ("source:second",)),
        "host-conflict-second",
    )
    product_graph.backend.set_relationships(
        (
            RelationshipInput(
                first.id,
                first.version,
                second.id,
                second.version,
                "contradicts",
                "different retry limits",
                "source:conflict",
            ),
        ),
        {first.id: first.version, second.id: second.version},
        "host-conflict-relation",
    )
    facade = ExpertiseOSService(
        product_graph.knowledge,
        product_graph.backend,
        product_graph.state,
        (),
    )

    result = facade.search_knowledge(SearchQuery("retry", 20, None, (), (), ()))

    assert result.status is ToolStatus.OK
    response = cast(RetrievalResponse, result.data)
    assert len(response.results) == 2
    assert any(item.conflicts for item in response.results)


def test_acceptance_corpus_covers_required_categories_subjects_and_conditions() -> None:
    document = cast(dict[str, object], json.loads(CORPUS.read_text(encoding="utf-8")))
    records = cast(list[dict[str, object]], document["records"])

    assert {str(item["category"]) for item in records} == {
        "declarative",
        "structural_procedural",
        "conditional_boundary",
        "causal_mechanistic",
        "episodic_tacit_experiential",
        "goal_metacognitive_normative",
    }
    assert {subject for item in records for subject in cast(list[str], item["subjects"])} == {
        "domain",
        "self",
        "ai",
    }
    assert {str(item["condition"]) for item in records} >= {
        "duplicate",
        "changed_condition",
        "contradiction",
        "uncertain_novelty",
        "unavailable_source",
        "malicious_content",
        "non_coding_task",
    }
