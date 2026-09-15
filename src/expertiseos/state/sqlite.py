#!/usr/bin/env python3
# Purpose: Persist minimal completed approval receipts in SQLite.

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from expertiseos.domain.errors import (
    ApprovalRejectedError,
    DomainValidationError,
    ReceiptConflictError,
    StaleVersionError,
)
from expertiseos.domain.models import ApprovalReceipt, LearnerState, PendingOperationKind
from expertiseos.learning.controls import (
    ApprovedKnowledgeRef,
    ControlSettings,
    DeferredActivity,
    DeferredStatus,
    ExclusionKind,
    PeriodProgress,
    ScopeExclusion,
    TargetPeriod,
)
from expertiseos.learning.evidence import (
    AdvancementThresholds,
    AssistanceLevel,
    EvidenceOutcome,
    LearnerEvidence,
)


class SQLiteState:
    """Own the small forward-only consent state schema."""

    def __init__(self, path: str | Path) -> None:
        self._connection = sqlite3.connect(str(path))
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.executescript(
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
            );
            CREATE TABLE IF NOT EXISTS learner_evidence (
                id TEXT PRIMARY KEY NOT NULL,
                knowledge_id TEXT NOT NULL,
                knowledge_version INTEGER NOT NULL,
                task_ref TEXT,
                session_id TEXT NOT NULL,
                criterion TEXT NOT NULL,
                outcome TEXT NOT NULL,
                assistance_level TEXT NOT NULL,
                scope TEXT,
                user_contribution TEXT,
                proposed_state TEXT NOT NULL,
                approved_state TEXT,
                is_meaningful_transfer INTEGER NOT NULL,
                approval_receipt_id TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (approval_receipt_id) REFERENCES approval_receipts(operation_id)
            );
            CREATE TABLE IF NOT EXISTS control_state (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                enabled INTEGER NOT NULL,
                learning_paused INTEGER NOT NULL,
                pause_until TEXT,
                target_period TEXT NOT NULL,
                reflection_target INTEGER NOT NULL,
                effort_limit TEXT NOT NULL,
                rest_interval_minutes INTEGER NOT NULL,
                fatigue_rest_until TEXT,
                timezone_id TEXT NOT NULL,
                recognized_passes INTEGER NOT NULL,
                explained_passes INTEGER NOT NULL,
                applied_passes INTEGER NOT NULL,
                transferred_passes INTEGER NOT NULL,
                autonomous_passes INTEGER NOT NULL,
                version INTEGER UNIQUE NOT NULL,
                approval_receipt_id TEXT UNIQUE NOT NULL,
                FOREIGN KEY (approval_receipt_id) REFERENCES approval_receipts(operation_id)
            );
            CREATE TABLE IF NOT EXISTS control_operations (
                approval_receipt_id TEXT PRIMARY KEY NOT NULL,
                expected_version INTEGER NOT NULL,
                settings_json TEXT NOT NULL,
                FOREIGN KEY (approval_receipt_id) REFERENCES approval_receipts(operation_id)
            );
            CREATE TABLE IF NOT EXISTS period_progress (
                period_key TEXT PRIMARY KEY NOT NULL,
                reflection_count INTEGER NOT NULL,
                effort_units TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS progress_events (
                event_id TEXT PRIMARY KEY NOT NULL,
                event_kind TEXT NOT NULL,
                period_key TEXT NOT NULL,
                units TEXT,
                FOREIGN KEY (period_key) REFERENCES period_progress(period_key)
            );
            CREATE TABLE IF NOT EXISTS scope_exclusions (
                id TEXT PRIMARY KEY NOT NULL,
                kind TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                approval_receipt_id TEXT UNIQUE NOT NULL,
                FOREIGN KEY (approval_receipt_id) REFERENCES approval_receipts(operation_id)
            );
            CREATE TABLE IF NOT EXISTS deferred_activities (
                id TEXT PRIMARY KEY NOT NULL,
                activity_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                approval_receipt_id TEXT UNIQUE NOT NULL,
                FOREIGN KEY (approval_receipt_id) REFERENCES approval_receipts(operation_id)
            );
            CREATE TABLE IF NOT EXISTS deferred_activity_refs (
                activity_id TEXT NOT NULL,
                knowledge_id TEXT NOT NULL,
                knowledge_version INTEGER NOT NULL,
                PRIMARY KEY (activity_id, knowledge_id, knowledge_version),
                FOREIGN KEY (activity_id) REFERENCES deferred_activities(id) ON DELETE CASCADE
            );
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

    def _require_receipt(
        self, operation_id: str, operation_kind: PendingOperationKind
    ) -> ApprovalReceipt:
        receipt = self.get_receipt(operation_id)
        if receipt is None or receipt.operation_kind is not operation_kind:
            raise ApprovalRejectedError("matching stored approval receipt required")
        return receipt

    @staticmethod
    def _require_limit(limit: int) -> None:
        if type(limit) is not int or not 1 <= limit <= 20:
            raise DomainValidationError("state query limit must be between 1 and 20")

    @staticmethod
    def _evidence_from_row(row: Sequence[object]) -> LearnerEvidence:
        return LearnerEvidence(
            str(row[0]),
            str(row[1]),
            int(str(row[2])),
            None if row[3] is None else str(row[3]),
            str(row[4]),
            str(row[5]),
            EvidenceOutcome(str(row[6])),
            AssistanceLevel(str(row[7])),
            None if row[8] is None else str(row[8]),
            None if row[9] is None else str(row[9]),
            LearnerState(str(row[10])),
            None if row[11] is None else LearnerState(str(row[11])),
            bool(row[12]),
            str(row[13]),
            datetime.fromisoformat(str(row[14])),
        )

    def insert_evidence_once(self, evidence: LearnerEvidence) -> LearnerEvidence:
        receipt = self._require_receipt(
            evidence.approval_receipt_id, PendingOperationKind.LEARNING_EVIDENCE
        )
        if (evidence.knowledge_id, evidence.knowledge_version) not in receipt.object_ids_versions:
            raise ApprovalRejectedError("receipt does not bind evidence object/version")
        values = (
            evidence.id,
            evidence.knowledge_id,
            evidence.knowledge_version,
            evidence.task_ref,
            evidence.session_id,
            evidence.criterion,
            evidence.outcome.value,
            evidence.assistance_level.value,
            evidence.scope,
            evidence.user_contribution,
            evidence.proposed_state.value,
            None if evidence.approved_state is None else evidence.approved_state.value,
            int(evidence.is_meaningful_transfer),
            evidence.approval_receipt_id,
            evidence.created_at.isoformat(),
        )
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO learner_evidence (
                        id, knowledge_id, knowledge_version, task_ref, session_id, criterion,
                        outcome, assistance_level, scope, user_contribution, proposed_state,
                        approved_state, is_meaningful_transfer, approval_receipt_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )
        except sqlite3.IntegrityError as error:
            existing = self._connection.execute(
                "SELECT * FROM learner_evidence WHERE id = ?", (evidence.id,)
            ).fetchone()
            if existing is None or self._evidence_from_row(existing) != evidence:
                raise ReceiptConflictError(
                    "evidence identity already has different input"
                ) from error
            return evidence
        return evidence

    def list_evidence(
        self,
        knowledge_id: str,
        version: int | None,
        scope: str | None,
        limit: int,
    ) -> tuple[LearnerEvidence, ...]:
        self._require_limit(limit)
        clauses = ["knowledge_id = ?"]
        values: list[object] = [knowledge_id]
        if version is not None:
            clauses.append("knowledge_version = ?")
            values.append(version)
        if scope is not None:
            clauses.append("scope = ?")
            values.append(scope)
        values.append(limit)
        rows = self._connection.execute(
            f"SELECT * FROM learner_evidence WHERE {' AND '.join(clauses)} "
            "ORDER BY created_at, id LIMIT ?",
            values,
        ).fetchall()
        return tuple(self._evidence_from_row(row) for row in rows)

    @staticmethod
    def _settings_document(settings: ControlSettings) -> str:
        document = {
            "enabled": settings.enabled,
            "learning_paused": settings.learning_paused,
            "pause_until": None
            if settings.pause_until is None
            else settings.pause_until.isoformat(),
            "target_period": settings.target_period.value,
            "reflection_target": settings.reflection_target,
            "effort_limit": str(settings.effort_limit),
            "rest_interval_minutes": settings.rest_interval_minutes,
            "fatigue_rest_until": None
            if settings.fatigue_rest_until is None
            else settings.fatigue_rest_until.isoformat(),
            "timezone_id": settings.timezone_id,
            "thresholds": settings.advancement_thresholds.as_tuple(),
            "version": settings.version,
        }
        return json.dumps(document, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _settings_from_document(document: str) -> ControlSettings:
        value = json.loads(document)
        thresholds = AdvancementThresholds(*(int(item) for item in value["thresholds"]))
        return ControlSettings(
            bool(value["enabled"]),
            bool(value["learning_paused"]),
            None
            if value["pause_until"] is None
            else datetime.fromisoformat(str(value["pause_until"])),
            TargetPeriod(str(value["target_period"])),
            int(value["reflection_target"]),
            Decimal(str(value["effort_limit"])),
            int(value["rest_interval_minutes"]),
            None
            if value["fatigue_rest_until"] is None
            else datetime.fromisoformat(str(value["fatigue_rest_until"])),
            str(value["timezone_id"]),
            thresholds,
            int(value["version"]),
        )

    def apply_control_change(
        self,
        expected_version: int,
        settings: ControlSettings,
        approval_receipt_id: str,
    ) -> ControlSettings:
        self._require_receipt(approval_receipt_id, PendingOperationKind.CONTROL_CHANGE)
        document = self._settings_document(settings)
        prior = self._connection.execute(
            "SELECT expected_version, settings_json FROM control_operations "
            "WHERE approval_receipt_id = ?",
            (approval_receipt_id,),
        ).fetchone()
        if prior is not None:
            if int(prior[0]) != expected_version or str(prior[1]) != document:
                raise ReceiptConflictError("control receipt already has different input")
            return self._settings_from_document(str(prior[1]))
        current = self.read_control_state()
        current_version = 0 if current is None else current.version
        if expected_version != current_version or settings.version != expected_version + 1:
            raise StaleVersionError("control version is stale")
        thresholds = settings.advancement_thresholds
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO control_state (
                    singleton, enabled, learning_paused, pause_until, target_period,
                    reflection_target, effort_limit, rest_interval_minutes,
                    fatigue_rest_until, timezone_id, recognized_passes, explained_passes,
                    applied_passes, transferred_passes, autonomous_passes, version,
                    approval_receipt_id
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(singleton) DO UPDATE SET
                    enabled=excluded.enabled,
                    learning_paused=excluded.learning_paused,
                    pause_until=excluded.pause_until,
                    target_period=excluded.target_period,
                    reflection_target=excluded.reflection_target,
                    effort_limit=excluded.effort_limit,
                    rest_interval_minutes=excluded.rest_interval_minutes,
                    fatigue_rest_until=excluded.fatigue_rest_until,
                    timezone_id=excluded.timezone_id,
                    recognized_passes=excluded.recognized_passes,
                    explained_passes=excluded.explained_passes,
                    applied_passes=excluded.applied_passes,
                    transferred_passes=excluded.transferred_passes,
                    autonomous_passes=excluded.autonomous_passes,
                    version=excluded.version,
                    approval_receipt_id=excluded.approval_receipt_id
                """,
                (
                    int(settings.enabled),
                    int(settings.learning_paused),
                    None if settings.pause_until is None else settings.pause_until.isoformat(),
                    settings.target_period.value,
                    settings.reflection_target,
                    str(settings.effort_limit),
                    settings.rest_interval_minutes,
                    None
                    if settings.fatigue_rest_until is None
                    else settings.fatigue_rest_until.isoformat(),
                    settings.timezone_id,
                    thresholds.recognized_passes,
                    thresholds.explained_passes,
                    thresholds.applied_passes,
                    thresholds.transferred_passes,
                    thresholds.autonomous_passes,
                    settings.version,
                    approval_receipt_id,
                ),
            )
            self._connection.execute(
                "INSERT INTO control_operations "
                "(approval_receipt_id, expected_version, settings_json) VALUES (?, ?, ?)",
                (approval_receipt_id, expected_version, document),
            )
        return settings

    def read_control_state(self) -> ControlSettings | None:
        row = self._connection.execute(
            """
            SELECT enabled, learning_paused, pause_until, target_period, reflection_target,
                   effort_limit, rest_interval_minutes, fatigue_rest_until, timezone_id,
                   recognized_passes, explained_passes, applied_passes, transferred_passes,
                   autonomous_passes, version
            FROM control_state WHERE singleton = 1
            """
        ).fetchone()
        if row is None:
            return None
        return ControlSettings(
            bool(row[0]),
            bool(row[1]),
            None if row[2] is None else datetime.fromisoformat(str(row[2])),
            TargetPeriod(str(row[3])),
            int(row[4]),
            Decimal(str(row[5])),
            int(row[6]),
            None if row[7] is None else datetime.fromisoformat(str(row[7])),
            str(row[8]),
            AdvancementThresholds(*(int(value) for value in row[9:14])),
            int(row[14]),
        )

    def read_control_approval_receipt_id(self) -> str | None:
        row = self._connection.execute(
            "SELECT approval_receipt_id FROM control_state WHERE singleton = 1"
        ).fetchone()
        return None if row is None else str(row[0])

    def restore_control_state(
        self, settings: ControlSettings, approval_receipt_id: str
    ) -> ControlSettings:
        """Restore one validated control snapshot without replaying change history."""
        self._require_receipt(approval_receipt_id, PendingOperationKind.CONTROL_CHANGE)
        current = self.read_control_state()
        current_receipt = self.read_control_approval_receipt_id()
        if current is not None:
            if current != settings or current_receipt != approval_receipt_id:
                raise ReceiptConflictError("restored control state conflicts with current state")
            return current
        thresholds = settings.advancement_thresholds
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO control_state (
                    singleton, enabled, learning_paused, pause_until, target_period,
                    reflection_target, effort_limit, rest_interval_minutes,
                    fatigue_rest_until, timezone_id, recognized_passes, explained_passes,
                    applied_passes, transferred_passes, autonomous_passes, version,
                    approval_receipt_id
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(settings.enabled),
                    int(settings.learning_paused),
                    None if settings.pause_until is None else settings.pause_until.isoformat(),
                    settings.target_period.value,
                    settings.reflection_target,
                    str(settings.effort_limit),
                    settings.rest_interval_minutes,
                    None
                    if settings.fatigue_rest_until is None
                    else settings.fatigue_rest_until.isoformat(),
                    settings.timezone_id,
                    thresholds.recognized_passes,
                    thresholds.explained_passes,
                    thresholds.applied_passes,
                    thresholds.transferred_passes,
                    thresholds.autonomous_passes,
                    settings.version,
                    approval_receipt_id,
                ),
            )
        return settings

    def read_period_progress(self, period_key: str) -> PeriodProgress:
        row = self._connection.execute(
            "SELECT reflection_count, effort_units FROM period_progress WHERE period_key = ?",
            (period_key,),
        ).fetchone()
        reflection_ids = tuple(
            str(row[0])
            for row in self._connection.execute(
                "SELECT event_id FROM progress_events "
                "WHERE period_key = ? AND event_kind = 'reflection' ORDER BY event_id",
                (period_key,),
            ).fetchall()
        )
        effort_ids = tuple(
            str(row[0])
            for row in self._connection.execute(
                "SELECT event_id FROM progress_events "
                "WHERE period_key = ? AND event_kind = 'effort' ORDER BY event_id",
                (period_key,),
            ).fetchall()
        )
        if row is None:
            return PeriodProgress(period_key, 0, Decimal("0"), reflection_ids, effort_ids)
        return PeriodProgress(
            period_key, int(row[0]), Decimal(str(row[1])), reflection_ids, effort_ids
        )

    def has_period_progress(self, period_key: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM period_progress WHERE period_key = ?", (period_key,)
        ).fetchone()
        return row is not None

    def _existing_progress_event(
        self, event_id: str, event_kind: str, period_key: str, units: str | None
    ) -> bool:
        prior = self._connection.execute(
            "SELECT event_kind, period_key, units FROM progress_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if prior is None:
            return False
        if (str(prior[0]), str(prior[1]), prior[2]) != (event_kind, period_key, units):
            raise ReceiptConflictError("progress event already has different input")
        return True

    def record_reflection_once(self, period_key: str, event_id: str) -> PeriodProgress:
        if not period_key or not event_id:
            raise DomainValidationError("period key and event id are required")
        if self._existing_progress_event(event_id, "reflection", period_key, None):
            return self.read_period_progress(period_key)
        with self._connection:
            self._connection.execute(
                "INSERT OR IGNORE INTO period_progress VALUES (?, 0, '0')", (period_key,)
            )
            self._connection.execute(
                "INSERT INTO progress_events VALUES (?, 'reflection', ?, NULL)",
                (event_id, period_key),
            )
            self._connection.execute(
                "UPDATE period_progress SET reflection_count = reflection_count + 1 "
                "WHERE period_key = ?",
                (period_key,),
            )
        return self.read_period_progress(period_key)

    def record_effort_once(self, period_key: str, event_id: str, units: Decimal) -> PeriodProgress:
        if not period_key or not event_id or units <= Decimal("0"):
            raise DomainValidationError("period key, event id, and positive effort are required")
        encoded = str(units)
        if self._existing_progress_event(event_id, "effort", period_key, encoded):
            return self.read_period_progress(period_key)
        with self._connection:
            self._connection.execute(
                "INSERT OR IGNORE INTO period_progress VALUES (?, 0, '0')", (period_key,)
            )
            current = self._connection.execute(
                "SELECT effort_units FROM period_progress WHERE period_key = ?", (period_key,)
            ).fetchone()
            assert current is not None
            total = Decimal(str(current[0])) + units
            self._connection.execute(
                "INSERT INTO progress_events VALUES (?, 'effort', ?, ?)",
                (event_id, period_key, encoded),
            )
            self._connection.execute(
                "UPDATE period_progress SET effort_units = ? WHERE period_key = ?",
                (str(total), period_key),
            )
        return self.read_period_progress(period_key)

    def read_effort_events(self, period_key: str) -> tuple[tuple[str, Decimal], ...]:
        rows = self._connection.execute(
            "SELECT event_id, units FROM progress_events "
            "WHERE period_key = ? AND event_kind = 'effort' ORDER BY event_id",
            (period_key,),
        ).fetchall()
        return tuple((str(row[0]), Decimal(str(row[1]))) for row in rows)

    def restore_period_progress(
        self,
        progress: PeriodProgress,
        effort_events: tuple[tuple[str, Decimal], ...],
        operation_id: str,
    ) -> PeriodProgress:
        """Restore a validated aggregate and its idempotency events."""
        if not operation_id.strip():
            raise DomainValidationError("restore operation id is required")
        if progress.reflection_count != len(progress.reflection_event_ids):
            raise DomainValidationError("reflection aggregate does not match event ids")
        if tuple(event_id for event_id, _ in effort_events) != tuple(
            sorted(progress.effort_event_ids)
        ):
            raise DomainValidationError("effort aggregate does not match event ids")
        if (
            any(units <= Decimal("0") for _, units in effort_events)
            or sum((units for _, units in effort_events), Decimal("0")) != progress.effort_units
        ):
            raise DomainValidationError("effort aggregate does not match event units")
        existing_row = self._connection.execute(
            "SELECT 1 FROM period_progress WHERE period_key = ?", (progress.period_key,)
        ).fetchone()
        if existing_row is not None:
            if (
                self.read_period_progress(progress.period_key) != progress
                or self.read_effort_events(progress.period_key) != effort_events
            ):
                raise ReceiptConflictError("restored progress conflicts with current state")
            return progress
        try:
            with self._connection:
                self._connection.execute(
                    "INSERT INTO period_progress VALUES (?, ?, ?)",
                    (progress.period_key, progress.reflection_count, str(progress.effort_units)),
                )
                self._connection.executemany(
                    "INSERT INTO progress_events VALUES (?, 'reflection', ?, NULL)",
                    ((event_id, progress.period_key) for event_id in progress.reflection_event_ids),
                )
                self._connection.executemany(
                    "INSERT INTO progress_events VALUES (?, 'effort', ?, ?)",
                    (
                        (event_id, progress.period_key, str(units))
                        for event_id, units in effort_events
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise ReceiptConflictError("restored progress event identity conflicts") from error
        return progress

    def _require_control_version(self, expected_version: int) -> ControlSettings:
        settings = self.read_control_state()
        if settings is None or settings.version != expected_version:
            raise StaleVersionError("control version is stale")
        return settings

    def replace_or_remove_exclusion(
        self,
        expected_version: int,
        exclusion_id: str,
        replacement: ScopeExclusion | None,
        approval_receipt_id: str,
    ) -> ScopeExclusion | None:
        self._require_receipt(approval_receipt_id, PendingOperationKind.CONTROL_CHANGE)
        self._require_control_version(expected_version)
        if replacement is None:
            with self._connection:
                self._connection.execute(
                    "DELETE FROM scope_exclusions WHERE id = ?", (exclusion_id,)
                )
                self._connection.execute(
                    "UPDATE control_state SET version = ?, approval_receipt_id = ? "
                    "WHERE singleton = 1",
                    (expected_version + 1, approval_receipt_id),
                )
            return None
        if replacement.id != exclusion_id:
            raise DomainValidationError("exclusion identity changed")
        if replacement.approval_receipt_id != approval_receipt_id:
            raise ApprovalRejectedError("exclusion does not match approval receipt")
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO scope_exclusions VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET kind=excluded.kind, value=excluded.value,
                    created_at=excluded.created_at,
                    approval_receipt_id=excluded.approval_receipt_id
                """,
                (
                    replacement.id,
                    replacement.kind.value,
                    replacement.value,
                    replacement.created_at.isoformat(),
                    replacement.approval_receipt_id,
                ),
            )
            self._connection.execute(
                "UPDATE control_state SET version = ?, approval_receipt_id = ? WHERE singleton = 1",
                (expected_version + 1, approval_receipt_id),
            )
        return replacement

    def list_exclusions(self, limit: int) -> tuple[ScopeExclusion, ...]:
        self._require_limit(limit)
        rows = self._connection.execute(
            "SELECT id, kind, value, created_at, approval_receipt_id "
            "FROM scope_exclusions ORDER BY created_at, id LIMIT ?",
            (limit,),
        ).fetchall()
        return tuple(
            ScopeExclusion(
                str(row[0]),
                ExclusionKind(str(row[1])),
                str(row[2]),
                datetime.fromisoformat(str(row[3])),
                str(row[4]),
            )
            for row in rows
        )

    def restore_exclusion(self, exclusion: ScopeExclusion) -> ScopeExclusion:
        """Restore one approved exclusion without changing snapshot control version."""
        self._require_receipt(exclusion.approval_receipt_id, PendingOperationKind.CONTROL_CHANGE)
        row = self._connection.execute(
            "SELECT id, kind, value, created_at, approval_receipt_id "
            "FROM scope_exclusions WHERE id = ?",
            (exclusion.id,),
        ).fetchone()
        if row is not None:
            existing = ScopeExclusion(
                str(row[0]),
                ExclusionKind(str(row[1])),
                str(row[2]),
                datetime.fromisoformat(str(row[3])),
                str(row[4]),
            )
            if existing != exclusion:
                raise ReceiptConflictError("restored exclusion conflicts with current state")
            return existing
        with self._connection:
            self._connection.execute(
                "INSERT INTO scope_exclusions VALUES (?, ?, ?, ?, ?)",
                (
                    exclusion.id,
                    exclusion.kind.value,
                    exclusion.value,
                    exclusion.created_at.isoformat(),
                    exclusion.approval_receipt_id,
                ),
            )
        return exclusion

    def insert_deferred_once(self, activity: DeferredActivity) -> DeferredActivity:
        receipt = self._require_receipt(
            activity.approval_receipt_id, PendingOperationKind.CONTROL_CHANGE
        )
        approved_refs = set(receipt.object_ids_versions)
        refs = {(item.knowledge_id, item.version) for item in activity.knowledge_refs}
        if not refs.issubset(approved_refs):
            raise ApprovalRejectedError("receipt does not bind deferred knowledge references")
        try:
            with self._connection:
                self._connection.execute(
                    "INSERT INTO deferred_activities VALUES (?, ?, ?, ?, ?)",
                    (
                        activity.id,
                        activity.activity_type,
                        activity.created_at.isoformat(),
                        activity.status.value,
                        activity.approval_receipt_id,
                    ),
                )
                self._connection.executemany(
                    "INSERT INTO deferred_activity_refs VALUES (?, ?, ?)",
                    (
                        (activity.id, item.knowledge_id, item.version)
                        for item in activity.knowledge_refs
                    ),
                )
        except sqlite3.IntegrityError as error:
            existing = self._get_deferred(activity.id)
            if existing != activity:
                raise ReceiptConflictError(
                    "deferred identity already has different input"
                ) from error
            return activity
        return activity

    def _get_deferred(self, activity_id: str) -> DeferredActivity | None:
        row = self._connection.execute(
            "SELECT id, activity_type, created_at, status, approval_receipt_id "
            "FROM deferred_activities WHERE id = ?",
            (activity_id,),
        ).fetchone()
        if row is None:
            return None
        refs = tuple(
            ApprovedKnowledgeRef(str(item[0]), int(item[1]))
            for item in self._connection.execute(
                "SELECT knowledge_id, knowledge_version FROM deferred_activity_refs "
                "WHERE activity_id = ? ORDER BY knowledge_id, knowledge_version",
                (activity_id,),
            ).fetchall()
        )
        return DeferredActivity(
            str(row[0]),
            refs,
            str(row[1]),
            datetime.fromisoformat(str(row[2])),
            DeferredStatus(str(row[3])),
            str(row[4]),
        )

    def remove_deferred(
        self, expected_version: int, activity: DeferredActivity
    ) -> DeferredActivity:
        receipt = self._require_receipt(
            activity.approval_receipt_id, PendingOperationKind.CONTROL_CHANGE
        )
        self._require_control_version(expected_version)
        if activity.status is not DeferredStatus.REMOVED:
            raise DomainValidationError("deferred removal must have removed status")
        current = self._get_deferred(activity.id)
        if current is None or current.knowledge_refs != activity.knowledge_refs:
            raise StaleVersionError("deferred activity is missing or changed")
        refs = {(item.knowledge_id, item.version) for item in activity.knowledge_refs}
        if not refs.issubset(set(receipt.object_ids_versions)):
            raise ApprovalRejectedError("receipt does not bind deferred knowledge references")
        with self._connection:
            self._connection.execute(
                "UPDATE deferred_activities SET status = ?, approval_receipt_id = ? WHERE id = ?",
                (activity.status.value, activity.approval_receipt_id, activity.id),
            )
            self._connection.execute(
                "UPDATE control_state SET version = ?, approval_receipt_id = ? WHERE singleton = 1",
                (expected_version + 1, activity.approval_receipt_id),
            )
        return activity

    def list_deferred(
        self, status: DeferredStatus | None, limit: int
    ) -> tuple[DeferredActivity, ...]:
        self._require_limit(limit)
        if status is None:
            rows = self._connection.execute(
                "SELECT id FROM deferred_activities ORDER BY created_at, id LIMIT ?", (limit,)
            ).fetchall()
        else:
            rows = self._connection.execute(
                "SELECT id FROM deferred_activities WHERE status = ? "
                "ORDER BY created_at, id LIMIT ?",
                (status.value, limit),
            ).fetchall()
        values = tuple(self._get_deferred(str(row[0])) for row in rows)
        return tuple(item for item in values if item is not None)

    def delete_learning_scope(
        self,
        object_refs: tuple[tuple[str, int], ...],
        remove_evidence_excerpts: bool,
        remove_deferred_activities: bool,
        operation_id: str,
    ) -> tuple[int, int]:
        """Apply an approved deletion scope to C004-owned records."""
        receipt = self._require_receipt(operation_id, PendingOperationKind.DELETE)
        if tuple(sorted(object_refs)) != tuple(sorted(receipt.object_ids_versions)):
            raise ApprovalRejectedError("delete scope differs from approval receipt")
        evidence_deleted = 0
        deferred_deleted = 0
        with self._connection:
            for knowledge_id, version in object_refs:
                if remove_evidence_excerpts:
                    cursor = self._connection.execute(
                        "DELETE FROM learner_evidence "
                        "WHERE knowledge_id = ? AND knowledge_version = ?",
                        (knowledge_id, version),
                    )
                    evidence_deleted += cursor.rowcount
                if remove_deferred_activities:
                    rows = self._connection.execute(
                        "SELECT activity_id FROM deferred_activity_refs "
                        "WHERE knowledge_id = ? AND knowledge_version = ?",
                        (knowledge_id, version),
                    ).fetchall()
                    for row in rows:
                        cursor = self._connection.execute(
                            "DELETE FROM deferred_activities WHERE id = ?", (str(row[0]),)
                        )
                        deferred_deleted += cursor.rowcount
        return evidence_deleted, deferred_deleted

    def table_names(self) -> tuple[str, ...]:
        rows: Sequence[tuple[str]] = self._connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
        return tuple(row[0] for row in rows)

    def close(self) -> None:
        self._connection.close()
