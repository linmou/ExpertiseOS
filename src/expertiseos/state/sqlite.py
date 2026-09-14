#!/usr/bin/env python3
# Purpose: Persist minimal completed approval receipts in SQLite.

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from expertiseos.domain.errors import ReceiptConflictError
from expertiseos.domain.models import ApprovalReceipt, PendingOperationKind


class SQLiteState:
    """Own the small forward-only consent state schema."""

    def __init__(self, path: str | Path) -> None:
        self._connection = sqlite3.connect(str(path))
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS approval_receipts (
                operation_id TEXT PRIMARY KEY NOT NULL,
                proposal_id TEXT NOT NULL,
                operation_kind TEXT NOT NULL,
                object_refs_json TEXT NOT NULL,
                content_digest TEXT NOT NULL,
                user_event_ref TEXT NOT NULL,
                adapter_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def record_receipt(self, receipt: ApprovalReceipt) -> ApprovalReceipt:
        existing = self.get_receipt(receipt.operation_id)
        if existing is not None:
            if existing != receipt:
                raise ReceiptConflictError("operation_id already has a different receipt")
            return existing
        object_refs = json.dumps(receipt.object_ids_versions, separators=(",", ":"))
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO approval_receipts (
                        operation_id, proposal_id, operation_kind, object_refs_json,
                        content_digest, user_event_ref, adapter_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        receipt.operation_id,
                        receipt.proposal_id,
                        receipt.operation_kind.value,
                        object_refs,
                        receipt.content_digest,
                        receipt.user_event_ref,
                        receipt.adapter_id,
                        receipt.created_at.isoformat(),
                    ),
                )
        except sqlite3.IntegrityError as error:
            existing = self.get_receipt(receipt.operation_id)
            if existing != receipt:
                raise ReceiptConflictError(
                    "operation_id already has a different receipt"
                ) from error
            assert existing is not None
            return existing
        return receipt

    def get_receipt(self, operation_id: str) -> ApprovalReceipt | None:
        row = self._connection.execute(
            """
            SELECT operation_id, proposal_id, operation_kind, object_refs_json,
                   content_digest, user_event_ref, adapter_id, created_at
            FROM approval_receipts WHERE operation_id = ?
            """,
            (operation_id,),
        ).fetchone()
        if row is None:
            return None
        refs_raw = json.loads(row[3])
        refs = tuple((str(item[0]), int(item[1])) for item in refs_raw)
        return ApprovalReceipt(
            str(row[0]),
            str(row[1]),
            PendingOperationKind(str(row[2])),
            refs,
            str(row[4]),
            str(row[5]),
            str(row[6]),
            datetime.fromisoformat(str(row[7])),
        )

    def table_names(self) -> tuple[str, ...]:
        rows: Sequence[tuple[str]] = self._connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
        return tuple(row[0] for row in rows)

    def close(self) -> None:
        self._connection.close()
