#!/usr/bin/env python3
# Purpose: Verify C008 AT-06, AT-09, and AT-12 shared-state and isolation behavior.

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import cast

from expertiseos.domain.models import CommitStatus, LearnerState
from expertiseos.hosts.claude_code import (
    ClaudeCapabilityEvidence,
    ClaudeCodeAdapter,
    ClaudeEnvironment,
    EvidenceResult,
)
from expertiseos.hosts.codex import CodexAdapter, CodexEnvironment
from expertiseos.knowledge.backend import (
    ApprovedKnowledgeInput,
    KnowledgeRecord,
    RelationshipInput,
    RetrievalResponse,
    SearchQuery,
)
from expertiseos.learning.controls import (
    ContextScope,
    ControlReason,
    PeriodProgress,
    default_daily_settings,
    resolve_controls,
)
from expertiseos.learning.evidence import (
    AdvancementThresholds,
    ApprovedObjectFact,
    LearningInspection,
)
from expertiseos.service import ExpertiseOSService, ToolStatus
from tests.consent_support import NOW, observation
from tests.e2e.conftest import ProductGraph

SCENARIO = Path(__file__).parents[2] / "examples/reference_scenarios/cross_host.json"
CLAUDE_ENVIRONMENT = ClaudeEnvironment(
    "2.1.241",
    "macOS 15.1.1 build 24B91",
    "arm64",
    "default",
)


def _approved(item: dict[str, object]) -> ApprovedKnowledgeInput:
    content = str(item["content"])
    return ApprovedKnowledgeInput(
        content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
        tuple(cast(list[str], item["categories"])),
        tuple(cast(list[str], item["subjects"])),
        str(item["applicability_scope"]),
        str(item["evidential_status"]),
        tuple(cast(list[str], item["source_refs"])),
        "user",
    )


def _claude_evidence() -> tuple[ClaudeCapabilityEvidence, ...]:
    return tuple(
        ClaudeCapabilityEvidence(
            CLAUDE_ENVIRONMENT,
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


def _adapters(product_graph: ProductGraph) -> tuple[CodexAdapter, ClaudeCodeAdapter]:
    codex = CodexAdapter(
        CodexEnvironment(
            "0.146.1",
            "macOS 15.1.1 build 24B91",
            "arm64",
            "workspace-write",
        ),
        "session-codex",
        product_graph.candidates,
        product_graph.grants,
    )
    claude = ClaudeCodeAdapter(
        "session-claude",
        CLAUDE_ENVIRONMENT,
        _claude_evidence(),
        product_graph.knowledge,
    )
    return codex, claude


def _register(product_graph: ProductGraph, proposal_id: str, grant_id: str) -> None:
    product_graph.knowledge.present(proposal_id)
    product_graph.knowledge.register_decision(
        proposal_id,
        grant_id,
        observation(user_event_ref=f"user-event:{proposal_id}"),
        NOW + timedelta(minutes=1),
    )


def test_at12_codex_and_claude_read_the_same_approved_state(
    product_graph: ProductGraph,
) -> None:
    fixture = json.loads(SCENARIO.read_text(encoding="utf-8"))
    items = cast(list[dict[str, object]], fixture["initial_approved_state"]["knowledge"])
    records = tuple(
        product_graph.backend.create_approved(_approved(item), f"seed:{item['stable_id']}")
        for item in items
    )
    relation = RelationshipInput(
        records[0].id,
        records[0].version,
        records[1].id,
        records[1].version,
        "supports",
        "fixture relation",
        "scenario:D",
    )
    product_graph.backend.set_relationships(
        (relation,),
        {record.id: record.version for record in records},
        "seed:relation",
    )
    codex, claude = _adapters(product_graph)
    facade = ExpertiseOSService(
        product_graph.knowledge,
        product_graph.backend,
        product_graph.state,
        (codex, claude),
    )
    query = SearchQuery("cross-host", 20, "repository", (), (), ())
    codex_result = facade.search_knowledge(query)
    controls = resolve_controls(
        default_daily_settings("UTC", 1),
        PeriodProgress("2026-09-14", 0, Decimal("0"), (), ()),
        NOW,
    )
    claude_result = claude.search(
        query,
        controls,
        ContextScope("terminal", "/workspace/project", claude.session_id),
        (),
    )

    assert codex_result.status is ToolStatus.OK
    codex_response = cast(RetrievalResponse, codex_result.data)
    assert claude_result == codex_response
    assert controls.reason is ControlReason.ACTIVE
    assert controls.approved_recall is True
    assert {result.knowledge_id for result in codex_response.results} == {
        record.id for record in records
    }
    assert {result.knowledge_id: result.version for result in codex_response.results} == {
        records[0].id: 2,
        records[1].id: 1,
    }
    assert {result.source_refs for result in codex_response.results} == {
        ("codex:user-event-1",),
        ("claude-code:user-event-1",),
    }
    assert any(result.relationships for result in codex_response.results)
    assert {result.evidential_status for result in codex_response.results} == {
        "observed",
        "uncertain",
    }
    for record, item in zip(records, items, strict=True):
        read_result = facade.get_knowledge(record.id, None, False)
        assert read_result.status is ToolStatus.OK
        current = cast(KnowledgeRecord, read_result.data)
        assert current.content == item["content"]
        assert current.source_refs == tuple(cast(list[str], item["source_refs"]))
    for adapter_id in (codex.adapter_id, claude.adapter_id):
        capabilities = facade.inspect_capabilities(adapter_id)
        assert capabilities.status is ToolStatus.OK
        available = {item.name: item.available for item in capabilities.capabilities}
        assert available["can_read"] is True
        assert available["can_search"] is True
        assert available["can_write"] is False


def test_at06_grant_cannot_cross_adapter_or_session(product_graph: ProductGraph) -> None:
    proposals = (
        ("proposal-source", "operation-source", "session-source", "codex"),
        ("proposal-host", "operation-host", "session-host", "claude-code"),
        ("proposal-session", "operation-session", "session-other", "codex"),
    )
    for proposal_id, operation_id, session_id, adapter_id in proposals:
        product_graph.knowledge.propose_create(
            proposal_id,
            operation_id,
            session_id,
            adapter_id,
            _approved(
                {
                    "content": proposal_id,
                    "categories": ["fact"],
                    "subjects": ["domain"],
                    "applicability_scope": "repository",
                    "evidential_status": "observed",
                    "source_refs": [f"{adapter_id}:user-event"],
                }
            ),
            NOW,
        )
        product_graph.knowledge.present(proposal_id)
    product_graph.knowledge.register_decision(
        "proposal-source",
        "grant-source",
        observation(user_event_ref="codex:user-event"),
        NOW + timedelta(minutes=1),
    )

    cross_host = product_graph.knowledge.commit("proposal-host", "grant-source", "operation-host")
    cross_session = product_graph.knowledge.commit(
        "proposal-session", "grant-source", "operation-session"
    )
    source = product_graph.knowledge.commit("proposal-source", "grant-source", "operation-source")

    assert cross_host.status is CommitStatus.REJECTED
    assert cross_session.status is CommitStatus.REJECTED
    assert source.status is CommitStatus.COMMITTED
    assert product_graph.state.get_receipt("operation-host") is None
    assert product_graph.state.get_receipt("operation-session") is None


def test_at12_second_version_three_commit_conflicts_with_version_four(
    product_graph: ProductGraph,
) -> None:
    seed = _approved(
        {
            "content": "version one",
            "categories": ["fact"],
            "subjects": ["domain"],
            "applicability_scope": "repository",
            "evidential_status": "observed",
            "source_refs": ["seed:user-event"],
        }
    )
    record = product_graph.backend.create_approved(seed, "seed:v1")
    for version in (2, 3):
        record = product_graph.backend.update_approved(
            record.id,
            version - 1,
            _approved(
                {
                    "content": f"version {version}",
                    "categories": ["fact"],
                    "subjects": ["domain"],
                    "applicability_scope": "repository",
                    "evidential_status": "observed",
                    "source_refs": ["seed:user-event"],
                }
            ),
            f"seed:v{version}",
        )
    for proposal_id, operation_id, adapter_id, content in (
        ("proposal-v4-first", "operation-v4-first", "codex", "version four first"),
        ("proposal-v4-second", "operation-v4-second", "claude-code", "version four second"),
    ):
        product_graph.knowledge.propose_revision(
            proposal_id,
            operation_id,
            f"session:{adapter_id}",
            adapter_id,
            record.id,
            3,
            _approved(
                {
                    "content": content,
                    "categories": ["fact"],
                    "subjects": ["domain"],
                    "applicability_scope": "repository",
                    "evidential_status": "observed",
                    "source_refs": [f"{adapter_id}:user-event"],
                }
            ),
            NOW,
        )
        _register(product_graph, proposal_id, f"grant:{proposal_id}")

    first = product_graph.knowledge.commit(
        "proposal-v4-first", "grant:proposal-v4-first", "operation-v4-first"
    )
    second = product_graph.knowledge.commit(
        "proposal-v4-second", "grant:proposal-v4-second", "operation-v4-second"
    )

    assert first.status is CommitStatus.COMMITTED
    assert first.records[0].version == 4
    assert second.status is CommitStatus.CONFLICT
    current = product_graph.backend.get(record.id)
    assert current is not None
    assert current.version == 4
    assert current.content == "version four first"


def test_at09_reflection_count_and_mastery_are_global_not_per_host(
    product_graph: ProductGraph,
) -> None:
    codex, claude = _adapters(product_graph)
    facade = ExpertiseOSService(
        product_graph.knowledge,
        product_graph.backend,
        product_graph.state,
        (codex, claude),
    )
    first = product_graph.state.record_reflection_once("2026-09-14", "reflection-global-1")
    repeated = product_graph.state.record_reflection_once("2026-09-14", "reflection-global-1")
    fact = ApprovedObjectFact("knowledge-shared", 1, "python", False)
    thresholds = AdvancementThresholds(1, 1, 1, 1, 2)
    codex_state = facade.inspect_learning_state(fact, thresholds, False, NOW)
    claude_state = facade.inspect_learning_state(fact, thresholds, False, NOW)

    assert first.reflection_count == repeated.reflection_count == 1
    assert first.reflection_event_ids == repeated.reflection_event_ids == ("reflection-global-1",)
    assert codex_state.status is claude_state.status is ToolStatus.OK
    assert codex_state.data == claude_state.data
    inspection = cast(LearningInspection, codex_state.data)
    assert inspection.summary.state is LearnerState.NEW
