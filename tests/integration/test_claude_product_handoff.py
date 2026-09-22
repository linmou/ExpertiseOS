#!/usr/bin/env python3
# Purpose: Verify E10 passes actual C006 events and capabilities into C008 behavior.

from __future__ import annotations

from pathlib import Path

from expertiseos.hosts.claude_code import (
    ADAPTER_ID,
    ClaudeCapabilityEvidence,
    ClaudeCodeAdapter,
    ClaudeEnvironment,
    ClaudeRawEvent,
    EvidenceResult,
    RawOrigin,
)
from expertiseos.hosts.contract import DecisionAction, DecisionBinding, DecisionRejection
from expertiseos.service import ExpertiseOSService, ToolStatus
from tests.consent_support import NOW
from tests.integration.product_handoff_support import build_product_handoff_graph


def test_actual_claude_output_is_consumed_by_c008_without_write_promotion(
    tmp_path: Path,
) -> None:
    graph = build_product_handoff_graph(tmp_path)
    try:
        environment = ClaudeEnvironment("2.1.241", "macOS 15.1.1 build 24B91", "arm64", "default")
        evidence = tuple(
            ClaudeCapabilityEvidence(
                environment,
                name,
                (),
                "e10-read" if name in {"can_read", "can_search"} else "e10-not-run",
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
        )
        adapter = ClaudeCodeAdapter("session-claude", environment, evidence, graph.knowledge)
        facade = ExpertiseOSService(graph.knowledge, graph.backend, graph.state, (adapter,))
        start = adapter.handle_raw_event(
            ClaudeRawEvent(
                "e10-start",
                "SessionStart",
                adapter.session_id,
                NOW,
                RawOrigin.LIFECYCLE,
                None,
                None,
            )
        )
        event = adapter.handle_raw_event(
            ClaudeRawEvent(
                "e10-save",
                "UserPromptSubmit",
                adapter.session_id,
                NOW,
                RawOrigin.USER,
                "Save",
                "actual-user:e10",
            )
        )
        binding = DecisionBinding(
            "e10-proposal",
            "create",
            ADAPTER_ID,
            adapter.session_id,
            "b" * 64,
            (),
            (DecisionAction.SAVE,),
        )
        adapter.set_active_binding(binding)
        observation = adapter.register_decision_if_unambiguous(event, binding)
        capabilities = facade.inspect_capabilities(ADAPTER_ID)

        assert start is adapter.events[0]
        assert event is adapter.events[1]
        assert capabilities.status is ToolStatus.OK
        assert capabilities.data is adapter.capabilities()
        assert {item.name: item.available for item in capabilities.capabilities}[
            "can_write"
        ] is False
        assert observation.matched is False
        assert observation.rejection is DecisionRejection.ACTION_NOT_ALLOWED
    finally:
        graph.state.close()
