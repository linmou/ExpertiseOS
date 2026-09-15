#!/usr/bin/env python3
# Purpose: Verify E09 passes actual C005 events and capabilities into C008 behavior.

from __future__ import annotations

from pathlib import Path

from expertiseos.hosts.codex import CodexAdapter, CodexEnvironment, normalize_hook
from expertiseos.hosts.contract import DecisionAction, DecisionBinding, DecisionRejection
from expertiseos.service import ExpertiseOSService, ToolStatus
from tests.consent_support import NOW
from tests.integration.product_handoff_support import build_product_handoff_graph


def test_actual_codex_output_is_consumed_by_c008_without_write_promotion(
    tmp_path: Path,
) -> None:
    graph = build_product_handoff_graph(tmp_path)
    try:
        adapter = CodexAdapter(
            CodexEnvironment(
                "0.146.1",
                "macOS 15.1.1 build 24B91",
                "arm64",
                "workspace-write",
            ),
            "session-codex",
            graph.candidates,
            graph.grants,
        )
        facade = ExpertiseOSService(graph.knowledge, graph.backend, graph.state, (adapter,))
        adapter.on_session_start(
            normalize_hook(
                {
                    "hook_event_name": "SessionStart",
                    "session_id": "session-codex",
                    "event_id": "e09-start",
                },
                NOW,
            )
        )
        event = normalize_hook(
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "session-codex",
                "turn_id": "e09-turn",
                "prompt": "Save",
            },
            NOW,
        )
        adapter.on_user_event(event)
        observation = adapter.register_decision_if_unambiguous(
            event,
            DecisionBinding(
                "e09-proposal",
                "create",
                adapter.adapter_id,
                adapter.session_id,
                "a" * 64,
                (),
                (DecisionAction.SAVE,),
            ),
        )
        capabilities = facade.inspect_capabilities(adapter.adapter_id)

        assert capabilities.status is ToolStatus.OK
        assert capabilities.data is adapter.capabilities()
        assert {item.name: item.available for item in capabilities.capabilities}[
            "can_write"
        ] is False
        assert event is adapter.events[-1]
        assert observation.matched is False
        assert observation.rejection is DecisionRejection.AMBIGUOUS_ACTION
    finally:
        graph.state.close()
