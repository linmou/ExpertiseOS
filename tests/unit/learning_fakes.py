#!/usr/bin/env python3
# Purpose: Provide approved C002/C003 facts for C004 learning and control tests.

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from expertiseos.domain.models import ApprovalReceipt, PendingOperationKind
from expertiseos.knowledge.backend import (
    IndexState,
    SearchMode,
    SearchResult,
    TrustLevel,
)

NOW = datetime(2026, 9, 14, 16, 0, tzinfo=UTC)


def receipt(
    knowledge_id: str = "knowledge-1",
    version: int = 1,
    operation_id: str = "evidence-operation-1",
) -> ApprovalReceipt:
    return ApprovalReceipt(
        operation_id,
        "proposal-1",
        PendingOperationKind.LEARNING_EVIDENCE,
        ((knowledge_id, version),),
        hashlib.sha256(b"approved evidence").hexdigest(),
        "user-event-1",
        "codex",
        NOW,
    )


def search_result(
    knowledge_id: str = "knowledge-1",
    version: int = 1,
    scope: str | None = "python",
    conflicts: tuple[str, ...] = (),
) -> SearchResult:
    return SearchResult(
        knowledge_id,
        version,
        "approved knowledge",
        ("procedure",),
        ("domain",),
        scope,
        "observed",
        ("event:1",),
        True,
        (),
        conflicts,
        TrustLevel.UNTRUSTED_DATA,
        SearchMode.KEYWORD,
        IndexState.DEGRADED,
    )
