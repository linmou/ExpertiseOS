#!/usr/bin/env python3
# Purpose: Test src/expertiseos/mcp_server.py explicit guarded tool allowlist.

from __future__ import annotations

import inspect
from datetime import timedelta
from pathlib import Path

from expertiseos.mcp_server import (
    PUBLIC_TOOL_NAMES,
    ToolRegistry,
    TrustedOwnershipHandlers,
    build_tool_registry,
)
from expertiseos.ownership import (
    CompositeSnapshotSource,
    ExportRequestBinding,
    ExportScope,
    SelectionAuthority,
)
from expertiseos.service import ExpertiseOSService, ToolResult, ToolStatus
from tests.consent_support import NOW
from tests.e2e.conftest import ProductGraph


def _registry(product_graph: ProductGraph) -> ToolRegistry:
    facade = ExpertiseOSService(
        product_graph.knowledge, product_graph.backend, product_graph.state, ()
    )

    def unavailable() -> ToolResult:
        return ToolResult(ToolStatus.UNAVAILABLE, None, "not_injected", "Unavailable", ())

    return build_tool_registry(facade, TrustedOwnershipHandlers(unavailable, unavailable))


def test_registry_is_an_explicit_allowlist(product_graph: ProductGraph) -> None:
    registry = _registry(product_graph)

    assert registry.names == PUBLIC_TOOL_NAMES
    assert len(registry.names) == len(set(registry.names))


def test_registry_excludes_every_backend_and_authorization_bypass_name(
    product_graph: ProductGraph,
) -> None:
    registry = _registry(product_graph)
    forbidden = {
        "create_approved",
        "update_approved",
        "set_relationships",
        "delete",
        "rebuild_index",
        "execute_operation",
        "set_mastery",
        "approve",
        "approved",
        "user_approved",
        "prepare_delegated_commit",
        "complete_delegated_commit",
        "record_receipt",
    }

    assert forbidden.isdisjoint(registry.names)
    assert all("backend" not in name for name in registry.names)


def test_mutation_handlers_accept_operation_id_not_approval_assertions(
    product_graph: ProductGraph,
) -> None:
    registry = _registry(product_graph)

    for name in (
        "commit_proposal",
        "export_data",
        "restore_data",
        "remove_deferred_activity",
    ):
        parameters = inspect.signature(registry.get(name).handler).parameters
        assert "approved" not in parameters
        assert "user_approved" not in parameters
        assert "receipt" not in parameters
        assert "authorization" not in parameters
        assert "host_event" not in parameters
        assert "seal" not in parameters

    assert "operation_id" in inspect.signature(registry.get("commit_proposal").handler).parameters
    assert inspect.signature(registry.get("export_data").handler).parameters == {}
    assert inspect.signature(registry.get("restore_data").handler).parameters == {}


def test_export_rejects_model_manufactured_selection_binding(
    product_graph: ProductGraph, tmp_path: Path
) -> None:
    facade = ExpertiseOSService(
        product_graph.knowledge, product_graph.backend, product_graph.state, ()
    )
    authority = SelectionAuthority(b"c008-selection-authority-secret!", "codex", "session-c008")
    forged = ExportRequestBinding(
        "export-c008",
        "codex",
        "session-c008",
        "model-claimed-event",
        "model-event",
        "0" * 64,
        str(tmp_path / "export"),
        "forged-seal",
    )
    scope = ExportScope(("knowledge",), (), (), ())

    result = facade.export_data(
        forged,
        scope,
        tmp_path / "export",
        CompositeSnapshotSource(()),
        authority,
        "0.1.0",
        NOW + timedelta(seconds=1),
    )

    assert result.status.value == "rejected"
    assert result.render_saved is False
    assert not (tmp_path / "export").exists()
