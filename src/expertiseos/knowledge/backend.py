#!/usr/bin/env python3
# Purpose: Define the narrow approved-data contract for knowledge backends.

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable


class BackendContractError(ValueError):
    """Raised for malformed backend contract values."""


class VersionConflictError(RuntimeError):
    """Raised when an expected knowledge version is stale."""


class IdempotencyConflictError(RuntimeError):
    """Raised when operation_id is reused with different command input."""


class KnowledgeStatus(StrEnum):
    ACTIVE = "active"
    RETIRED = "retired"


class StoreState(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class IndexState(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    REBUILDING = "rebuilding"
    UNAVAILABLE = "unavailable"


class SearchMode(StrEnum):
    LOCAL_SEMANTIC = "local_semantic"
    KEYWORD = "keyword"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ApprovedKnowledgeInput:
    content: str
    content_digest: str
    categories: tuple[str, ...]
    subjects: tuple[str, ...]
    applicability_scope: str | None
    evidential_status: str | None
    source_refs: tuple[str, ...]
    contribution_origin: str

    def __post_init__(self) -> None:
        if not self.content or not self.content_digest:
            raise BackendContractError("approved content and digest are required")
        expected_digest = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
        if self.content_digest != expected_digest:
            raise BackendContractError("content digest does not match approved content")
        if not self.subjects:
            raise BackendContractError("at least one subject is required")
        if self.contribution_origin not in {"user", "assistant", "joint"}:
            raise BackendContractError("invalid contribution origin")


@dataclass(frozen=True)
class RelationshipInput:
    source_id: str
    source_version: int
    target_id: str
    target_version: int
    type: str
    explanation: str | None
    source_ref: str | None

    def __post_init__(self) -> None:
        if not self.source_id or not self.target_id or not self.type:
            raise BackendContractError("relationship endpoints and type are required")
        if self.source_version < 1 or self.target_version < 1:
            raise BackendContractError("relationship versions must be positive")


@dataclass(frozen=True)
class KnowledgeRecord:
    id: str
    version: int
    content: str
    content_digest: str
    categories: tuple[str, ...]
    subjects: tuple[str, ...]
    applicability_scope: str | None
    evidential_status: str | None
    source_refs: tuple[str, ...]
    contribution_origin: str
    status: KnowledgeStatus
    relationships: tuple[RelationshipInput, ...]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class SearchQuery:
    text: str
    limit: int
    scope: str | None

    def __post_init__(self) -> None:
        if not self.text:
            raise BackendContractError("search text is required")
        if self.limit < 1:
            raise BackendContractError("search limit must be positive")


@dataclass(frozen=True)
class SearchResult:
    knowledge_id: str
    version: int
    excerpt: str
    source_refs: tuple[str, ...]
    relationships: tuple[RelationshipInput, ...]
    conflicts: tuple[str, ...]
    match_mode: SearchMode
    index_state: IndexState


@dataclass(frozen=True)
class BackendHealth:
    canonical_store: StoreState
    index: IndexState
    search_mode: SearchMode
    details: tuple[str, ...]


@dataclass(frozen=True)
class DeleteResult:
    knowledge_id: str
    deleted_versions: int


@dataclass(frozen=True)
class RebuildResult:
    indexed_records: int
    index_state: IndexState


@runtime_checkable
class KnowledgeBackend(Protocol):
    def create_approved(
        self, value: ApprovedKnowledgeInput, operation_id: str
    ) -> KnowledgeRecord: ...

    def get(
        self,
        knowledge_id: str,
        version: int | None = None,
        include_retired: bool = False,
    ) -> KnowledgeRecord | None: ...

    def get_current_versions(self, knowledge_ids: tuple[str, ...]) -> Mapping[str, int]: ...

    def search(self, query: SearchQuery) -> tuple[SearchResult, ...]: ...

    def update_approved(
        self,
        knowledge_id: str,
        expected_version: int,
        value: ApprovedKnowledgeInput,
        operation_id: str,
    ) -> KnowledgeRecord: ...

    def set_relationships(
        self,
        relationships: tuple[RelationshipInput, ...],
        expected_versions: Mapping[str, int],
        operation_id: str,
    ) -> tuple[KnowledgeRecord, ...]: ...

    def retire(
        self, knowledge_id: str, expected_version: int, operation_id: str
    ) -> KnowledgeRecord: ...

    def delete(
        self, knowledge_id: str, expected_version: int, operation_id: str
    ) -> DeleteResult: ...

    def rebuild_index(self) -> RebuildResult: ...

    def health(self) -> BackendHealth: ...
