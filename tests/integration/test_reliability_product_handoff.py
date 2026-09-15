#!/usr/bin/env python3
# Purpose: Verify E11 passes actual C007 ownership and fallback results through C008.

from __future__ import annotations

from pathlib import Path
from typing import cast

from expertiseos.knowledge.backend import RetrievalResponse, SearchMode, SearchQuery
from expertiseos.ownership import (
    BackendSnapshotSource,
    CompositeSnapshotSource,
    ExportResult,
    ExportScope,
    KnowledgeRef,
    SelectionAuthority,
)
from expertiseos.service import ExpertiseOSService, ToolStatus
from tests.backend_support import approved
from tests.consent_support import NOW
from tests.integration.fixtures.reliability_fixtures import user_event
from tests.integration.product_handoff_support import build_product_handoff_graph


def test_actual_c007_export_and_c003_fallback_feed_c008_results(
    tmp_path: Path,
) -> None:
    graph = build_product_handoff_graph(tmp_path)
    try:
        facade = ExpertiseOSService(graph.knowledge, graph.backend, graph.state, ())
        record = graph.backend.create_approved(
            approved("reliable portable knowledge", None, ("fact",), ("domain",), ("e11",)),
            "e11-create",
        )
        scope = ExportScope(
            ("knowledge",),
            (KnowledgeRef(record.id, record.version),),
            (),
            (),
        )
        destination = tmp_path / "e11-export"
        authority = SelectionAuthority(
            b"e11-selection-authority-secret-value!", "adapter-1", "session-1"
        )
        binding = authority.issue_export(
            user_event("e11-export"), "e11-export-operation", scope, destination
        )
        exported = facade.export_data(
            binding,
            scope,
            destination,
            CompositeSnapshotSource((BackendSnapshotSource(graph.backend),)),
            authority,
            "0.1.0",
            NOW,
        )
        export_result = cast(ExportResult, exported.data)

        assert exported.status is ToolStatus.COMMITTED
        assert export_result.operation_id == binding.operation_id
        assert export_result.export_id
        assert destination.joinpath("manifest.json").exists()

        graph.cli.fail_search = True
        degraded = facade.search_knowledge(SearchQuery("portable", 1, None, (), (), ()))
        response = cast(RetrievalResponse, degraded.data)
        assert degraded.status is ToolStatus.DEGRADED
        assert response.mode is SearchMode.KEYWORD
        assert response.results[0].knowledge_id == record.id
    finally:
        graph.state.close()
