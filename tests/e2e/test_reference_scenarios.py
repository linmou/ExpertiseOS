#!/usr/bin/env python3
# Purpose: Validate and execute C008 reference scenarios A through D on promoted services.

from __future__ import annotations

import dataclasses
import hashlib
import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import cast

from expertiseos.domain.models import CandidateState, CommitResult
from expertiseos.hosts.claude_code import (
    ClaudeCapabilityEvidence,
    ClaudeCodeAdapter,
    ClaudeEnvironment,
    EvidenceResult,
)
from expertiseos.hosts.codex import CodexAdapter, CodexEnvironment
from expertiseos.knowledge.backend import ApprovedKnowledgeInput, RetrievalResponse, SearchQuery
from expertiseos.learning.controls import (
    ControlReason,
    PeriodProgress,
    default_daily_settings,
    resolve_controls,
)
from expertiseos.service import ExpertiseOSService, ToolStatus
from tests.consent_support import NOW, observation
from tests.e2e.conftest import ProductGraph

SCENARIOS = Path(__file__).parents[2] / "examples/reference_scenarios"
FILES = {
    "A": "new_observation.json",
    "B": "conflict.json",
    "C": "fatigue.json",
    "D": "cross_host.json",
}


def _load(scenario_id: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads((SCENARIOS / FILES[scenario_id]).read_text(encoding="utf-8")),
    )


def _approved(
    content: str,
    source_ref: str,
    evidential_status: str,
) -> ApprovedKnowledgeInput:
    return ApprovedKnowledgeInput(
        content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
        ("procedure",),
        ("domain",),
        "repository",
        evidential_status,
        (source_ref,),
        "user",
    )


def _grant(product_graph: ProductGraph, proposal_id: str, grant_id: str) -> None:
    product_graph.knowledge.register_decision(
        proposal_id,
        grant_id,
        observation(user_event_ref=f"user:{proposal_id}"),
        NOW + timedelta(minutes=1),
    )


def _facade(product_graph: ProductGraph) -> ExpertiseOSService:
    return ExpertiseOSService(
        product_graph.knowledge,
        product_graph.backend,
        product_graph.state,
        (),
    )


def test_reference_scenario_documents_are_complete_and_non_executable() -> None:
    required = {
        "scenario_id",
        "title",
        "requirements",
        "acceptance_tests",
        "initial_approved_state",
        "events",
        "expected_visible_results",
        "expected_persistent_delta",
        "expected_volatile_end_state",
    }

    scenarios = tuple(_load(scenario_id) for scenario_id in FILES)

    assert {item["scenario_id"] for item in scenarios} == set(FILES)
    for scenario in scenarios:
        assert set(scenario) == required
        assert scenario["title"]
        assert cast(list[object], scenario["requirements"])
        assert cast(list[object], scenario["acceptance_tests"])
        assert isinstance(scenario["initial_approved_state"], dict)
        assert cast(list[object], scenario["events"])
        assert cast(list[object], scenario["expected_visible_results"])
        assert isinstance(scenario["expected_persistent_delta"], dict)
        assert isinstance(scenario["expected_volatile_end_state"], dict)
        assert "command" not in json.dumps(scenario).casefold()


def test_scenario_a_saves_now_and_reflects_later(product_graph: ProductGraph) -> None:
    scenario = _load("A")
    expected = cast(dict[str, object], scenario["expected_persistent_delta"])
    facade = _facade(product_graph)
    proposal = facade.propose_create_knowledge(
        "scenario-a-proposal",
        "scenario-a-operation",
        "scenario-a-session",
        "claude-code",
        _approved(str(expected["content"]), "claude:user-save-a", "observed"),
        NOW,
    )
    assert proposal.status is ToolStatus.OK
    _grant(product_graph, "scenario-a-proposal", "scenario-a-grant")

    saved = facade.commit_proposal(
        "scenario-a-proposal", "scenario-a-grant", "scenario-a-operation", {}
    )
    before_reflection = product_graph.state.read_period_progress("2026-09-14")
    reflected = product_graph.state.record_reflection_once("2026-09-14", "reflection-a-1")

    assert saved.status is ToolStatus.COMMITTED
    assert saved.render_saved is True
    commit = cast(CommitResult, saved.data)
    assert len(commit.records) == expected["knowledge_added"]
    assert before_reflection.reflection_count == 0
    assert reflected.reflection_count == expected["reflection_count"]
    candidate = product_graph.candidates.get("scenario-a-proposal")
    grant = product_graph.grants.get("scenario-a-grant")
    assert candidate is not None and candidate.state is CandidateState.APPROVED
    assert grant is not None and grant.consumed_at is not None


def test_scenario_b_keeps_coexist_revision_and_decline_distinct(
    product_graph: ProductGraph,
) -> None:
    scenario = _load("B")
    initial = cast(dict[str, object], scenario["initial_approved_state"])
    initial_note = cast(list[dict[str, object]], initial["knowledge"])[0]
    events = cast(list[dict[str, object]], scenario["events"])
    original = product_graph.backend.create_approved(
        _approved(
            str(initial_note["content"]),
            cast(list[str], initial_note["source_refs"])[0],
            "observed",
        ),
        "scenario-b-seed",
    )
    facade = _facade(product_graph)
    coexist = facade.propose_create_knowledge(
        "scenario-b-coexist",
        "scenario-b-coexist-operation",
        "scenario-b-session",
        "codex",
        _approved(str(events[0]["content"]), "codex:user-coexist", "conditional"),
        NOW,
    )
    assert coexist.status is ToolStatus.OK
    _grant(product_graph, "scenario-b-coexist", "scenario-b-coexist-grant")
    coexist_result = facade.commit_proposal(
        "scenario-b-coexist",
        "scenario-b-coexist-grant",
        "scenario-b-coexist-operation",
        {},
    )
    revision = facade.propose_revision(
        "scenario-b-revision",
        "scenario-b-revision-operation",
        "scenario-b-session",
        "codex",
        original.id,
        original.version,
        _approved(str(events[1]["content"]), "codex:user-revision", "observed"),
        NOW,
    )
    assert revision.status is ToolStatus.OK
    _grant(product_graph, "scenario-b-revision", "scenario-b-revision-grant")
    revision_result = facade.commit_proposal(
        "scenario-b-revision",
        "scenario-b-revision-grant",
        "scenario-b-revision-operation",
        {original.id: original.version},
    )
    declined = facade.propose_create_knowledge(
        "scenario-b-decline",
        "scenario-b-decline-operation",
        "scenario-b-session",
        "codex",
        _approved(str(events[2]["content"]), "codex:user-decline", "unsupported"),
        NOW,
    )
    assert declined.status is ToolStatus.OK
    decline_result = facade.decline_proposal("scenario-b-decline", "unsafe-replacement")

    assert coexist_result.status is ToolStatus.COMMITTED
    assert revision_result.status is ToolStatus.COMMITTED
    revised = product_graph.backend.get(original.id)
    assert revised is not None
    assert revised.version == 2
    assert revised.content == events[1]["content"]
    assert decline_result.status is ToolStatus.OK
    assert product_graph.candidates.get("scenario-b-decline").state is (  # type: ignore[union-attr]
        CandidateState.DECLINED
    )
    matches = product_graph.knowledge.search(SearchQuery("retries", 20, "repository", (), (), ()))
    assert len(matches.results) == 2
    assert all(result.excerpt != events[2]["content"] for result in matches.results)


def test_scenario_c_fatigue_precedes_target_without_disabling_recall() -> None:
    scenario = _load("C")
    initial = cast(dict[str, object], scenario["initial_approved_state"])
    controls = cast(dict[str, object], initial["controls"])
    settings = dataclasses.replace(
        default_daily_settings("UTC", 1),
        fatigue_rest_until=NOW + timedelta(minutes=cast(int, controls["fatigue_rest_minutes"])),
    )
    progress = PeriodProgress(
        "2026-09-14",
        cast(int, controls["reflection_count"]),
        Decimal("0"),
        ("reflection-c-1",),
        (),
    )

    resting = resolve_controls(settings, progress, NOW)
    after_rest = resolve_controls(settings, progress, NOW + timedelta(minutes=61))

    assert resting.reason is ControlReason.FATIGUE_REST
    assert resting.approved_recall is True
    assert (resting.observe, resting.prompt_collection, resting.proactive_exercises) == (
        False,
        False,
        False,
    )
    assert after_rest.reason is ControlReason.TARGET_SATISFIED
    assert after_rest.approved_recall is True
    assert after_rest.proactive_exercises is False


def test_scenario_d_uses_shared_state_and_isolated_volatile_stores(
    product_graph: ProductGraph,
) -> None:
    scenario = _load("D")
    initial = cast(dict[str, object], scenario["initial_approved_state"])
    notes = cast(list[dict[str, object]], initial["knowledge"])
    for note in notes:
        product_graph.backend.create_approved(
            _approved(
                str(note["content"]),
                cast(list[str], note["source_refs"])[0],
                str(note["evidential_status"]),
            ),
            f"scenario-d:{note['stable_id']}",
        )
    codex = CodexAdapter(
        CodexEnvironment(
            "0.146.1",
            "macOS 15.1.1 build 24B91",
            "arm64",
            "workspace-write",
        ),
        "scenario-d-codex",
        product_graph.candidates,
        product_graph.grants,
    )
    claude_environment = ClaudeEnvironment(
        "2.1.241",
        "macOS 15.1.1 build 24B91",
        "arm64",
        "default",
    )
    evidence = tuple(
        ClaudeCapabilityEvidence(
            claude_environment,
            name,
            (),
            "c006-read-evidence" if name in {"can_read", "can_search"} else "",
            EvidenceResult.PASS if name in {"can_read", "can_search"} else EvidenceResult.NOT_RUN,
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
    )
    claude = ClaudeCodeAdapter(
        "scenario-d-claude", claude_environment, evidence, product_graph.knowledge
    )
    codex_facade = ExpertiseOSService(
        product_graph.knowledge,
        product_graph.backend,
        product_graph.state,
        (codex,),
    )
    claude_facade = ExpertiseOSService(
        product_graph.knowledge,
        product_graph.backend,
        product_graph.state,
        (claude,),
    )
    query = SearchQuery("cross-host", 20, "repository", (), (), ())
    codex_result = codex_facade.search_knowledge(query)
    claude_result = claude_facade.search_knowledge(query)
    first = product_graph.state.record_reflection_once("2026-09-14", "reflection-global-1")
    second = product_graph.state.record_reflection_once("2026-09-14", "reflection-global-1")

    assert codex_result.status is claude_result.status is ToolStatus.OK
    assert cast(RetrievalResponse, codex_result.data) == cast(RetrievalResponse, claude_result.data)
    assert first.reflection_count == second.reflection_count == 1
    assert product_graph.candidates.get("scenario-d-codex") is None
    assert product_graph.grants.get("scenario-d-claude") is None
