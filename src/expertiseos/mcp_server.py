#!/usr/bin/env python3
# Purpose: Expose the explicit guarded expertiseOS tool allowlist to local hosts.

"""Local host tool registrations for expertiseOS."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from expertiseos.service import ExpertiseOSService, ToolResult

type ToolHandler = Callable[..., ToolResult]

PUBLIC_TOOL_NAMES = (
    "search_knowledge",
    "get_knowledge",
    "inspect_learning_state",
    "inspect_controls",
    "inspect_capabilities",
    "health",
    "propose_create_knowledge",
    "propose_revision",
    "propose_relation_change",
    "propose_learning_evidence",
    "decline_proposal",
    "commit_proposal",
    "propose_control_change",
    "propose_retire_or_delete",
    "export_data",
    "restore_data",
    "remove_deferred_activity",
)


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    handler: ToolHandler


@dataclass(frozen=True)
class TrustedOwnershipHandlers:
    export_data: ToolHandler
    restore_data: ToolHandler


class ToolRegistry:
    """Hold the exact local tool allowlist; it is not itself a host-facing generic tool."""

    def __init__(self, definitions: tuple[ToolDefinition, ...]) -> None:
        names = tuple(definition.name for definition in definitions)
        if names != PUBLIC_TOOL_NAMES or len(names) != len(set(names)):
            raise ValueError("tool registry must match the public allowlist exactly")
        self._definitions = definitions
        self._by_name = {definition.name: definition for definition in definitions}

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(definition.name for definition in self._definitions)

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._by_name[name]
        except KeyError as error:
            raise KeyError(f"tool is not registered: {name}") from error


def build_tool_registry(
    service: ExpertiseOSService,
    ownership: TrustedOwnershipHandlers,
) -> ToolRegistry:
    """Bind explicit service methods without exposing backend or authorization shortcuts."""
    return ToolRegistry(
        (
            ToolDefinition("search_knowledge", service.search_knowledge),
            ToolDefinition("get_knowledge", service.get_knowledge),
            ToolDefinition("inspect_learning_state", service.inspect_learning_state),
            ToolDefinition("inspect_controls", service.inspect_controls),
            ToolDefinition("inspect_capabilities", service.inspect_capabilities),
            ToolDefinition("health", service.health),
            ToolDefinition("propose_create_knowledge", service.propose_create_knowledge),
            ToolDefinition("propose_revision", service.propose_revision),
            ToolDefinition("propose_relation_change", service.propose_relation_change),
            ToolDefinition("propose_learning_evidence", service.propose_learning_evidence),
            ToolDefinition("decline_proposal", service.decline_proposal),
            ToolDefinition("commit_proposal", service.commit_proposal),
            ToolDefinition("propose_control_change", service.propose_control_change),
            ToolDefinition("propose_retire_or_delete", service.propose_retire_or_delete),
            ToolDefinition("export_data", ownership.export_data),
            ToolDefinition("restore_data", ownership.restore_data),
            ToolDefinition("remove_deferred_activity", service.remove_deferred_activity),
        )
    )
