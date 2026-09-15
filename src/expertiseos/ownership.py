#!/usr/bin/env python3
# Purpose: Implement portable ownership operations over approved expertiseOS state.

from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum, StrEnum
from pathlib import Path, PurePosixPath
from typing import Protocol, cast

from expertiseos.domain.models import ApprovalReceipt, LearnerState, PendingOperationKind
from expertiseos.hosts.contract import EventKind, HostEvent
from expertiseos.knowledge.backend import KnowledgeBackend, KnowledgeRecord, KnowledgeStatus
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
from expertiseos.state.sqlite import SQLiteState

SCHEMA_VERSION = 1
ALLOWED_RECORD_TYPES = frozenset(
    {
        "knowledge",
        "relationship",
        "source_reference",
        "approval_receipt",
        "learner_evidence",
        "learner_summary",
        "control",
        "progress",
        "scope_exclusion",
        "deferred_activity",
    }
)
RESTORE_ORDER = (
    "knowledge",
    "source_reference",
    "relationship",
    "approval_receipt",
    "learner_evidence",
    "learner_summary",
    "control",
    "progress",
    "scope_exclusion",
    "deferred_activity",
)


class OwnershipError(ValueError):
    """Raised when an ownership request or portable bundle is invalid."""


class OwnershipStatus(StrEnum):
    COMMITTED = "committed"
    REJECTED = "rejected"
    CONFLICT = "conflict"
    INCOMPLETE = "incomplete"
    REPAIR_REQUIRED = "repair_required"


class CollisionPolicy(StrEnum):
    REJECT_DIVERGENT = "reject_divergent"


class UninstallDataChoice(StrEnum):
    KEEP = "keep"
    DELETE = "delete"


@dataclass(frozen=True)
class KnowledgeRef:
    knowledge_id: str
    version: int

    def __post_init__(self) -> None:
        _require_text(self.knowledge_id, "knowledge id")
        if self.version < 1:
            raise OwnershipError("knowledge version must be positive")


@dataclass(frozen=True)
class ExportScope:
    record_types: tuple[str, ...]
    knowledge_refs: tuple[KnowledgeRef, ...]
    receipt_operation_ids: tuple[str, ...]
    period_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.record_types or not set(self.record_types).issubset(ALLOWED_RECORD_TYPES):
            raise OwnershipError("export scope contains unsupported record types")
        if len(self.record_types) != len(set(self.record_types)):
            raise OwnershipError("export record types must be unique")


@dataclass(frozen=True)
class ExportRequestBinding:
    operation_id: str
    adapter_id: str
    session_id: str
    user_event_ref: str
    event_id: str
    scope_digest: str
    destination_ref: str
    seal: str


@dataclass(frozen=True)
class RestoreRequestBinding:
    operation_id: str
    adapter_id: str
    session_id: str
    user_event_ref: str
    event_id: str
    export_id: str
    manifest_digest: str
    collision_policy: CollisionPolicy
    seal: str


@dataclass(frozen=True)
class ExportSection:
    record_type: str
    records: tuple[Mapping[str, object], ...]

    def __post_init__(self) -> None:
        if self.record_type not in ALLOWED_RECORD_TYPES:
            raise OwnershipError("unsupported export record type")


@dataclass(frozen=True)
class ExportResult:
    status: OwnershipStatus
    operation_id: str
    export_id: str | None
    destination: Path | None
    manifest_digest: str | None
    record_counts: tuple[tuple[str, int], ...]
    error_code: str | None


@dataclass(frozen=True)
class RestoreCollision:
    record_type: str
    identity: str
    incoming_version: int
    local_digest: str
    incoming_digest: str


@dataclass(frozen=True)
class RestorePlan:
    export_id: str
    manifest_digest: str
    sections: tuple[ExportSection, ...]
    collisions: tuple[RestoreCollision, ...]
    identical_count: int
    validation_errors: tuple[str, ...]


@dataclass(frozen=True)
class RestoreResult:
    status: OwnershipStatus
    operation_id: str
    restored_counts: tuple[tuple[str, int], ...]
    identical_count: int
    error_code: str | None


@dataclass(frozen=True)
class DeletionScope:
    object_refs: tuple[KnowledgeRef, ...]
    remove_relationships: bool
    remove_evidence_excerpts: bool
    remove_deferred_activities: bool
    external_limits: tuple[str, ...]


@dataclass(frozen=True)
class DeletionPlan:
    operation_id: str
    object_refs: tuple[KnowledgeRef, ...]
    remove_relationships: bool
    remove_evidence_excerpts: bool
    remove_deferred_activities: bool
    external_limits: tuple[str, ...]


@dataclass(frozen=True)
class DeletionTargetResult:
    target: str
    completed: bool
    detail: str


@dataclass(frozen=True)
class DeletionResult:
    status: OwnershipStatus
    operation_id: str
    targets: tuple[DeletionTargetResult, ...]
    external_limits: tuple[str, ...]


@dataclass(frozen=True)
class UninstallPlan:
    choice: UninstallDataChoice
    remove_host_integrations: bool
    unregister_service: bool
    deletion_plan: DeletionPlan | None


class ApprovedSnapshotSource(Protocol):
    def snapshot(self, scope: ExportScope) -> tuple[ExportSection, ...]: ...


class ExistingIdentityLookup(Protocol):
    def digest_for(self, record_type: str, identity: str, version: int) -> str | None: ...


class RestoreTarget(Protocol):
    def restore_section(
        self, record_type: str, records: tuple[Mapping[str, object], ...], operation_id: str
    ) -> int: ...

    def rebuild_index(self) -> None: ...


class LearningDeletionTarget(Protocol):
    def delete_learning_scope(
        self,
        refs: tuple[KnowledgeRef, ...],
        remove_evidence_excerpts: bool,
        remove_deferred_activities: bool,
        operation_id: str,
    ) -> tuple[DeletionTargetResult, ...]: ...


def _require_text(value: str, name: str) -> None:
    if not value or not value.strip():
        raise OwnershipError(f"{name} is required")


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _jsonable(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_jsonable(item) for item in value]
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise OwnershipError(f"unsupported portable value: {type(value).__name__}")


def scope_digest(scope: ExportScope) -> str:
    return _digest(_jsonable(scope))


def destination_ref(destination: Path) -> str:
    return str(destination.expanduser().resolve(strict=False))


class SelectionAuthority:
    """Issue sealed bindings only from normalized actual-user events."""

    def __init__(self, secret: bytes, adapter_id: str, session_id: str) -> None:
        if len(secret) < 32:
            raise OwnershipError("selection authority secret must be at least 32 bytes")
        _require_text(adapter_id, "adapter id")
        _require_text(session_id, "session id")
        self._secret = secret
        self._adapter_id = adapter_id
        self._session_id = session_id
        self._issued_events: set[str] = set()
        self._consumed_operations: set[str] = set()

    def _accept(self, event: HostEvent, operation_id: str) -> None:
        _require_text(operation_id, "operation id")
        if event.kind is not EventKind.USER_INPUT or not event.user_input_ref:
            raise OwnershipError("actual user selection event required")
        if event.adapter_id != self._adapter_id or event.session_id != self._session_id:
            raise OwnershipError("selection event is outside authority session")
        if event.event_id in self._issued_events:
            raise OwnershipError("selection event was already used")
        self._issued_events.add(event.event_id)

    def _seal(self, values: Sequence[str]) -> str:
        return hmac.new(self._secret, "\x1f".join(values).encode(), hashlib.sha256).hexdigest()

    def issue_export(
        self, event: HostEvent, operation_id: str, scope: ExportScope, destination: Path
    ) -> ExportRequestBinding:
        self._accept(event, operation_id)
        assert event.user_input_ref is not None
        digest = scope_digest(scope)
        target = destination_ref(destination)
        values = (
            "export",
            operation_id,
            event.adapter_id,
            event.session_id,
            event.user_input_ref,
            event.event_id,
            digest,
            target,
        )
        return ExportRequestBinding(*values[1:], self._seal(values))

    def issue_restore(
        self,
        event: HostEvent,
        operation_id: str,
        plan: RestorePlan,
        collision_policy: CollisionPolicy,
    ) -> RestoreRequestBinding:
        self._accept(event, operation_id)
        assert event.user_input_ref is not None
        values = (
            "restore",
            operation_id,
            event.adapter_id,
            event.session_id,
            event.user_input_ref,
            event.event_id,
            plan.export_id,
            plan.manifest_digest,
            collision_policy.value,
        )
        return RestoreRequestBinding(*values[1:8], collision_policy, self._seal(values))

    def verify_export(
        self, binding: ExportRequestBinding, scope: ExportScope, destination: Path
    ) -> None:
        digest = scope_digest(scope)
        target = destination_ref(destination)
        if binding.scope_digest != digest or binding.destination_ref != target:
            raise OwnershipError("request binding fields were altered")
        values = (
            "export",
            binding.operation_id,
            binding.adapter_id,
            binding.session_id,
            binding.user_event_ref,
            binding.event_id,
            digest,
            target,
        )
        self._verify(binding.operation_id, binding.seal, values)

    def verify_restore(self, binding: RestoreRequestBinding, plan: RestorePlan) -> None:
        if binding.export_id != plan.export_id or binding.manifest_digest != plan.manifest_digest:
            raise OwnershipError("request binding fields were altered")
        values = (
            "restore",
            binding.operation_id,
            binding.adapter_id,
            binding.session_id,
            binding.user_event_ref,
            binding.event_id,
            plan.export_id,
            plan.manifest_digest,
            binding.collision_policy.value,
        )
        self._verify(binding.operation_id, binding.seal, values)

    def _verify(self, operation_id: str, seal: str, values: Sequence[str]) -> None:
        if values[2] != self._adapter_id or values[3] != self._session_id:
            raise OwnershipError("request binding is outside authority session")
        if operation_id in self._consumed_operations:
            raise OwnershipError("request binding was already consumed")
        if not hmac.compare_digest(seal, self._seal(values)):
            raise OwnershipError("request binding fields were altered")
        self._consumed_operations.add(operation_id)


class CompositeSnapshotSource:
    def __init__(self, sources: tuple[ApprovedSnapshotSource, ...]) -> None:
        self._sources = sources

    def snapshot(self, scope: ExportScope) -> tuple[ExportSection, ...]:
        merged: dict[str, list[Mapping[str, object]]] = {}
        for source in self._sources:
            for section in source.snapshot(scope):
                merged.setdefault(section.record_type, []).extend(section.records)
        return tuple(
            ExportSection(record_type, tuple(merged.get(record_type, ())))
            for record_type in scope.record_types
        )


class BackendSnapshotSource:
    def __init__(self, backend: KnowledgeBackend) -> None:
        self._backend = backend

    def snapshot(self, scope: ExportScope) -> tuple[ExportSection, ...]:
        knowledge: list[Mapping[str, object]] = []
        relationships: list[Mapping[str, object]] = []
        source_refs: list[Mapping[str, object]] = []
        for ref in scope.knowledge_refs:
            record = self._backend.get(ref.knowledge_id, ref.version, include_retired=True)
            if record is None:
                raise OwnershipError(f"approved knowledge is missing: {ref.knowledge_id}")
            document = cast(dict[str, object], _jsonable(record))
            knowledge.append(document)
            for relation in record.relationships:
                relationships.append(cast(dict[str, object], _jsonable(relation)))
            for index, source_ref in enumerate(record.source_refs):
                source_refs.append(
                    {
                        "id": f"{record.id}:{record.version}:{index}",
                        "version": 1,
                        "knowledge_id": record.id,
                        "knowledge_version": record.version,
                        "value": source_ref,
                    }
                )
        values = {
            "knowledge": tuple(knowledge),
            "relationship": tuple(relationships),
            "source_reference": tuple(source_refs),
        }
        return tuple(
            ExportSection(kind, values[kind]) for kind in scope.record_types if kind in values
        )


class SQLiteSnapshotSource:
    """Read approved C002/C004 state through public bounded inspection methods."""

    def __init__(self, state: SQLiteState) -> None:
        self._state = state

    def snapshot(self, scope: ExportScope) -> tuple[ExportSection, ...]:
        receipts = tuple(
            receipt
            for operation_id in scope.receipt_operation_ids
            if (receipt := self._state.get_receipt(operation_id)) is not None
        )
        evidence = tuple(
            item
            for ref in scope.knowledge_refs
            for item in self._state.list_evidence(ref.knowledge_id, ref.version, None, 20)
        )
        settings = self._state.read_control_state()
        control: tuple[object, ...] = ()
        if settings is not None:
            control_record = cast(dict[str, object], _jsonable(settings))
            control_record["approval_receipt_id"] = self._state.read_control_approval_receipt_id()
            control = (control_record,)
        progress: list[Mapping[str, object]] = []
        for key in scope.period_keys:
            if not self._state.has_period_progress(key):
                continue
            record = cast(dict[str, object], _jsonable(self._state.read_period_progress(key)))
            record["effort_events"] = [
                [event_id, str(units)] for event_id, units in self._state.read_effort_events(key)
            ]
            progress.append(record)
        values: dict[str, tuple[object, ...]] = {
            "approval_receipt": receipts,
            "learner_evidence": evidence,
            "learner_summary": (),
            "control": control,
            "progress": tuple(progress),
            "scope_exclusion": self._state.list_exclusions(20),
            "deferred_activity": self._state.list_deferred(None, 20),
        }
        return tuple(
            ExportSection(
                record_type,
                tuple(cast(dict[str, object], _jsonable(record)) for record in values[record_type]),
            )
            for record_type in scope.record_types
            if record_type in values
        )


def _record_text(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise OwnershipError(f"portable {key} is invalid")
    return value


def _record_int(record: Mapping[str, object], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise OwnershipError(f"portable {key} is invalid")
    return value


def _record_bool(record: Mapping[str, object], key: str) -> bool:
    value = record.get(key)
    if not isinstance(value, bool):
        raise OwnershipError(f"portable {key} is invalid")
    return value


def _record_optional_text(record: Mapping[str, object], key: str) -> str | None:
    value = record.get(key)
    if value is not None and not isinstance(value, str):
        raise OwnershipError(f"portable {key} is invalid")
    return value


def _record_text_tuple(record: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = record.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise OwnershipError(f"portable {key} is invalid")
    return tuple(value)


def _record_refs(record: Mapping[str, object], key: str) -> tuple[tuple[str, int], ...]:
    value = record.get(key)
    if not isinstance(value, list):
        raise OwnershipError(f"portable {key} is invalid")
    refs: list[tuple[str, int]] = []
    for item in value:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not isinstance(item[1], int)
            or isinstance(item[1], bool)
        ):
            raise OwnershipError(f"portable {key} is invalid")
        refs.append((item[0], item[1]))
    return tuple(refs)


def _parse_receipt(record: Mapping[str, object]) -> ApprovalReceipt:
    return ApprovalReceipt(
        _record_text(record, "operation_id"),
        _record_text(record, "proposal_id"),
        PendingOperationKind(_record_text(record, "operation_kind")),
        _record_refs(record, "object_ids_versions"),
        _record_text(record, "content_digest"),
        _record_text(record, "user_event_ref"),
        _record_text(record, "adapter_id"),
        datetime.fromisoformat(_record_text(record, "created_at")),
    )


def _parse_evidence(record: Mapping[str, object]) -> LearnerEvidence:
    approved_state = _record_optional_text(record, "approved_state")
    return LearnerEvidence(
        _record_text(record, "id"),
        _record_text(record, "knowledge_id"),
        _record_int(record, "knowledge_version"),
        _record_optional_text(record, "task_ref"),
        _record_text(record, "session_id"),
        _record_text(record, "criterion"),
        EvidenceOutcome(_record_text(record, "outcome")),
        AssistanceLevel(_record_text(record, "assistance_level")),
        _record_optional_text(record, "scope"),
        _record_optional_text(record, "user_contribution"),
        LearnerState(_record_text(record, "proposed_state")),
        None if approved_state is None else LearnerState(approved_state),
        _record_bool(record, "is_meaningful_transfer"),
        _record_text(record, "approval_receipt_id"),
        datetime.fromisoformat(_record_text(record, "created_at")),
    )


def _parse_control(record: Mapping[str, object]) -> tuple[ControlSettings, str]:
    thresholds = record.get("advancement_thresholds")
    if not isinstance(thresholds, dict):
        raise OwnershipError("portable advancement_thresholds is invalid")
    pause_until = _record_optional_text(record, "pause_until")
    fatigue_until = _record_optional_text(record, "fatigue_rest_until")
    settings = ControlSettings(
        _record_bool(record, "enabled"),
        _record_bool(record, "learning_paused"),
        None if pause_until is None else datetime.fromisoformat(pause_until),
        TargetPeriod(_record_text(record, "target_period")),
        _record_int(record, "reflection_target"),
        Decimal(_record_text(record, "effort_limit")),
        _record_int(record, "rest_interval_minutes"),
        None if fatigue_until is None else datetime.fromisoformat(fatigue_until),
        _record_text(record, "timezone_id"),
        AdvancementThresholds(
            _record_int(thresholds, "recognized_passes"),
            _record_int(thresholds, "explained_passes"),
            _record_int(thresholds, "applied_passes"),
            _record_int(thresholds, "transferred_passes"),
            _record_int(thresholds, "autonomous_passes"),
        ),
        _record_int(record, "version"),
    )
    return settings, _record_text(record, "approval_receipt_id")


def _parse_progress(
    record: Mapping[str, object],
) -> tuple[PeriodProgress, tuple[tuple[str, Decimal], ...]]:
    raw_events = record.get("effort_events")
    if not isinstance(raw_events, list):
        raise OwnershipError("portable effort_events is invalid")
    effort_events: list[tuple[str, Decimal]] = []
    for item in raw_events:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not isinstance(item[1], str)
        ):
            raise OwnershipError("portable effort_events is invalid")
        effort_events.append((item[0], Decimal(item[1])))
    progress = PeriodProgress(
        _record_text(record, "period_key"),
        _record_int(record, "reflection_count"),
        Decimal(_record_text(record, "effort_units")),
        _record_text_tuple(record, "reflection_event_ids"),
        _record_text_tuple(record, "effort_event_ids"),
    )
    return progress, tuple(effort_events)


def _parse_exclusion(record: Mapping[str, object]) -> ScopeExclusion:
    return ScopeExclusion(
        _record_text(record, "id"),
        ExclusionKind(_record_text(record, "kind")),
        _record_text(record, "value"),
        datetime.fromisoformat(_record_text(record, "created_at")),
        _record_text(record, "approval_receipt_id"),
    )


def _parse_deferred(record: Mapping[str, object]) -> DeferredActivity:
    raw_refs = record.get("knowledge_refs")
    if not isinstance(raw_refs, list):
        raise OwnershipError("portable knowledge_refs is invalid")
    refs: list[ApprovedKnowledgeRef] = []
    for raw_ref in raw_refs:
        if not isinstance(raw_ref, dict):
            raise OwnershipError("portable knowledge_refs is invalid")
        refs.append(
            ApprovedKnowledgeRef(
                _record_text(raw_ref, "knowledge_id"),
                _record_int(raw_ref, "version"),
            )
        )
    return DeferredActivity(
        _record_text(record, "id"),
        tuple(refs),
        _record_text(record, "activity_type"),
        datetime.fromisoformat(_record_text(record, "created_at")),
        DeferredStatus(_record_text(record, "status")),
        _record_text(record, "approval_receipt_id"),
    )


def _validate_sqlite_record(record_type: str, record: Mapping[str, object]) -> None:
    if record_type == "approval_receipt":
        _parse_receipt(record)
    elif record_type == "learner_evidence":
        _parse_evidence(record)
    elif record_type == "control":
        _parse_control(record)
    elif record_type == "progress":
        _parse_progress(record)
    elif record_type == "scope_exclusion":
        _parse_exclusion(record)
    elif record_type == "deferred_activity":
        _parse_deferred(record)
    elif record_type == "learner_summary":
        raise OwnershipError("learner summaries must be derived after restore")


class SQLiteSnapshotIdentityLookup:
    """Resolve identity digests from the actual destination SQLite state."""

    def __init__(self, state: SQLiteState, scope: ExportScope) -> None:
        self._digests: dict[tuple[str, str, int], str] = {}
        for section in SQLiteSnapshotSource(state).snapshot(scope):
            for record in section.records:
                identity, version = _identity(section.record_type, record)
                self._digests[(section.record_type, identity, version)] = _digest(record)

    def digest_for(self, record_type: str, identity: str, version: int) -> str | None:
        return self._digests.get((record_type, identity, version))


class SQLiteLearningRestoreTarget:
    """Apply validated C002/C004 portable sections to the shared SQLite state."""

    def __init__(self, state: SQLiteState) -> None:
        self._state = state

    def restore_section(
        self,
        record_type: str,
        records: tuple[Mapping[str, object], ...],
        operation_id: str,
    ) -> int:
        if record_type == "approval_receipt":
            for record in records:
                self._state.record_receipt(_parse_receipt(record))
        elif record_type == "learner_evidence":
            for record in records:
                self._state.insert_evidence_once(_parse_evidence(record))
        elif record_type == "control":
            for record in records:
                settings, receipt_id = _parse_control(record)
                self._state.restore_control_state(settings, receipt_id)
        elif record_type == "progress":
            for record in records:
                progress, effort_events = _parse_progress(record)
                self._state.restore_period_progress(progress, effort_events, operation_id)
        elif record_type == "scope_exclusion":
            for record in records:
                self._state.restore_exclusion(_parse_exclusion(record))
        elif record_type == "deferred_activity":
            for record in records:
                self._state.insert_deferred_once(_parse_deferred(record))
        elif record_type == "learner_summary" and not records:
            return 0
        else:
            raise OwnershipError(f"SQLite restore does not own {record_type}")
        return len(records)

    def rebuild_index(self) -> None:
        return None


class SQLiteLearningDeletionTarget:
    """Apply C007 approved deletion plans to actual C004 SQLite state."""

    def __init__(self, state: SQLiteState) -> None:
        self._state = state

    def delete_learning_scope(
        self,
        refs: tuple[KnowledgeRef, ...],
        remove_evidence_excerpts: bool,
        remove_deferred_activities: bool,
        operation_id: str,
    ) -> tuple[DeletionTargetResult, ...]:
        evidence, deferred = self._state.delete_learning_scope(
            tuple((item.knowledge_id, item.version) for item in refs),
            remove_evidence_excerpts,
            remove_deferred_activities,
            operation_id,
        )
        return (
            DeletionTargetResult("learner_evidence", True, str(evidence)),
            DeletionTargetResult("deferred_activity", True, str(deferred)),
        )


def receipt_sections(
    receipts: tuple[ApprovalReceipt, ...], scope: ExportScope
) -> tuple[ExportSection, ...]:
    allowed = set(scope.receipt_operation_ids)
    records = tuple(
        cast(dict[str, object], _jsonable(receipt))
        for receipt in receipts
        if receipt.operation_id in allowed
    )
    return (ExportSection("approval_receipt", records),)


def export_approved(
    binding: ExportRequestBinding,
    scope: ExportScope,
    destination: Path,
    source: ApprovedSnapshotSource,
    authority: SelectionAuthority,
    product_version: str,
    created_at: datetime,
) -> ExportResult:
    try:
        authority.verify_export(binding, scope, destination)
        _require_text(product_version, "product version")
        if destination.exists():
            raise OwnershipError("export destination already exists")
        sections = source.snapshot(scope)
        by_type = {section.record_type: section for section in sections}
        if set(by_type) != set(scope.record_types) or len(by_type) != len(sections):
            raise OwnershipError("snapshot did not provide the exact approved export scope")
        temporary = Path(tempfile.mkdtemp(prefix=".expertiseos-export-", dir=destination.parent))
        descriptors: list[dict[str, object]] = []
        try:
            for record_type in scope.record_types:
                section = by_type[record_type]
                path = f"{record_type}.jsonl"
                payload = b"".join(
                    _canonical_bytes(_jsonable(record)) + b"\n" for record in section.records
                )
                (temporary / path).write_bytes(payload)
                descriptors.append(
                    {
                        "record_type": record_type,
                        "path": path,
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "bytes": len(payload),
                        "count": len(section.records),
                    }
                )
            export_id = hashlib.sha256(
                f"{binding.operation_id}\x1f{created_at.isoformat()}".encode()
            ).hexdigest()[:24]
            manifest = {
                "schema_version": SCHEMA_VERSION,
                "export_id": export_id,
                "created_at": created_at.isoformat(),
                "source_product_version": product_version,
                "files": descriptors,
            }
            manifest_bytes = _canonical_bytes(manifest)
            (temporary / "manifest.json").write_bytes(manifest_bytes)
            os.replace(temporary, destination)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        return ExportResult(
            OwnershipStatus.COMMITTED,
            binding.operation_id,
            export_id,
            destination,
            hashlib.sha256(manifest_bytes).hexdigest(),
            tuple((item.record_type, len(item.records)) for item in sections),
            None,
        )
    except Exception as error:
        return ExportResult(
            OwnershipStatus.REJECTED,
            binding.operation_id,
            None,
            None,
            None,
            (),
            error.__class__.__name__,
        )


def _safe_bundle_path(root: Path, raw: object) -> Path:
    if not isinstance(raw, str) or not raw:
        raise OwnershipError("manifest path is invalid")
    pure = PurePosixPath(raw)
    if pure.is_absolute() or ".." in pure.parts or len(pure.parts) != 1:
        raise OwnershipError("manifest path escapes bundle")
    return root / raw


def _identity(record_type: str, record: Mapping[str, object]) -> tuple[str, int]:
    for key in ("id", "operation_id", "period_key"):
        value = record.get(key)
        if isinstance(value, str) and value:
            version = record.get("version", 1)
            if not isinstance(version, int) or version < 1:
                raise OwnershipError("portable record version is invalid")
            return value, version
    if record_type == "relationship":
        values = tuple(
            record.get(key)
            for key in ("source_id", "source_version", "target_id", "target_version", "type")
        )
        if (
            isinstance(values[0], str)
            and bool(values[0])
            and isinstance(values[1], int)
            and values[1] > 0
            and isinstance(values[2], str)
            and bool(values[2])
            and isinstance(values[3], int)
            and values[3] > 0
            and isinstance(values[4], str)
            and bool(values[4])
        ):
            return ":".join(str(value) for value in values), 1
    if record_type == "control":
        version = record.get("version")
        if isinstance(version, int) and version > 0:
            return "control", version
    if record_type == "learner_summary":
        identity = record.get("knowledge_id")
        version = record.get("knowledge_version")
        if isinstance(identity, str) and isinstance(version, int) and version > 0:
            return identity, version
    raise OwnershipError("portable record lacks a stable identity")


def validate_restore(source: Path, lookup: ExistingIdentityLookup) -> RestorePlan:
    errors: list[str] = []
    collisions: list[RestoreCollision] = []
    sections: list[ExportSection] = []
    identical_count = 0
    export_id = ""
    manifest_digest = ""
    try:
        manifest_bytes = (source / "manifest.json").read_bytes()
        manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
        manifest = json.loads(manifest_bytes)
        if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
            raise OwnershipError("unsupported export manifest schema")
        export_id_value = manifest.get("export_id")
        if not isinstance(export_id_value, str) or not export_id_value:
            raise OwnershipError("export id is required")
        export_id = export_id_value
        files = manifest.get("files")
        if not isinstance(files, list) or not files:
            raise OwnershipError("manifest files are required")
        seen: set[str] = set()
        for descriptor in files:
            if not isinstance(descriptor, dict):
                raise OwnershipError("manifest descriptor is invalid")
            record_type = descriptor.get("record_type")
            if not isinstance(record_type, str) or record_type not in ALLOWED_RECORD_TYPES:
                raise OwnershipError("manifest record type is invalid")
            if record_type in seen:
                raise OwnershipError("manifest record type is duplicated")
            seen.add(record_type)
            path = _safe_bundle_path(source, descriptor.get("path"))
            payload = path.read_bytes()
            if descriptor.get("bytes") != len(payload):
                raise OwnershipError("manifest byte count mismatch")
            if descriptor.get("sha256") != hashlib.sha256(payload).hexdigest():
                raise OwnershipError("manifest digest mismatch")
            records: list[Mapping[str, object]] = []
            parsed_count = 0
            for line in payload.splitlines():
                parsed_count += 1
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise OwnershipError("portable record is not an object")
                record = cast(dict[str, object], value)
                identity, version = _identity(record_type, record)
                _validate_sqlite_record(record_type, record)
                incoming = _digest(record)
                local = lookup.digest_for(record_type, identity, version)
                if local is not None and local != incoming:
                    collisions.append(
                        RestoreCollision(record_type, identity, version, local, incoming)
                    )
                elif local == incoming:
                    identical_count += 1
                else:
                    records.append(record)
            if descriptor.get("count") != parsed_count:
                raise OwnershipError("manifest record count mismatch")
            sections.append(ExportSection(record_type, tuple(records)))
    except Exception as error:
        errors.append(error.__class__.__name__)
    return RestorePlan(
        export_id,
        manifest_digest,
        tuple(sections),
        tuple(collisions),
        identical_count,
        tuple(errors),
    )


def restore_validated(
    plan: RestorePlan,
    binding: RestoreRequestBinding,
    authority: SelectionAuthority,
    target: RestoreTarget,
) -> RestoreResult:
    try:
        authority.verify_restore(binding, plan)
        if binding.collision_policy is not CollisionPolicy.REJECT_DIVERGENT:
            raise OwnershipError("unsupported collision policy")
        if plan.validation_errors:
            raise OwnershipError("restore plan has validation errors")
        if plan.collisions:
            return RestoreResult(
                OwnershipStatus.CONFLICT, binding.operation_id, (), plan.identical_count, None
            )
        counts: list[tuple[str, int]] = []
        for record_type in RESTORE_ORDER:
            section = next(
                (item for item in plan.sections if item.record_type == record_type), None
            )
            if section is not None and section.records:
                restored = target.restore_section(
                    record_type, section.records, binding.operation_id
                )
                counts.append((record_type, restored))
        try:
            target.rebuild_index()
        except Exception as error:
            return RestoreResult(
                OwnershipStatus.REPAIR_REQUIRED,
                binding.operation_id,
                tuple(counts),
                plan.identical_count,
                error.__class__.__name__,
            )
        return RestoreResult(
            OwnershipStatus.COMMITTED,
            binding.operation_id,
            tuple(counts),
            plan.identical_count,
            None,
        )
    except Exception as error:
        return RestoreResult(
            OwnershipStatus.REJECTED, binding.operation_id, (), 0, error.__class__.__name__
        )


def plan_delete(scope: DeletionScope, receipt: ApprovalReceipt) -> DeletionPlan:
    if receipt.operation_kind is not PendingOperationKind.DELETE:
        raise OwnershipError("delete approval receipt required")
    refs = tuple((item.knowledge_id, item.version) for item in scope.object_refs)
    if tuple(sorted(refs)) != tuple(sorted(receipt.object_ids_versions)):
        raise OwnershipError("delete scope differs from approved object versions")
    return DeletionPlan(
        receipt.operation_id,
        scope.object_refs,
        scope.remove_relationships,
        scope.remove_evidence_excerpts,
        scope.remove_deferred_activities,
        scope.external_limits,
    )


def execute_delete(
    plan: DeletionPlan,
    backend: KnowledgeBackend,
    learning_target: LearningDeletionTarget,
) -> DeletionResult:
    targets: list[DeletionTargetResult] = []
    for index, ref in enumerate(plan.object_refs):
        operation_id = f"{plan.operation_id}:knowledge:{index}"
        try:
            result = backend.delete(ref.knowledge_id, ref.version, operation_id)
            targets.append(
                DeletionTargetResult(
                    f"knowledge:{ref.knowledge_id}", True, str(result.deleted_versions)
                )
            )
        except Exception as error:
            targets.append(
                DeletionTargetResult(
                    f"knowledge:{ref.knowledge_id}", False, error.__class__.__name__
                )
            )
    try:
        targets.extend(
            learning_target.delete_learning_scope(
                plan.object_refs,
                plan.remove_evidence_excerpts,
                plan.remove_deferred_activities,
                plan.operation_id,
            )
        )
    except Exception as error:
        targets.append(DeletionTargetResult("learning_state", False, error.__class__.__name__))
    status = (
        OwnershipStatus.COMMITTED
        if targets and all(item.completed for item in targets)
        else OwnershipStatus.INCOMPLETE
    )
    return DeletionResult(status, plan.operation_id, tuple(targets), plan.external_limits)


def retire_approved(receipt: ApprovalReceipt, backend: KnowledgeBackend) -> KnowledgeRecord:
    if receipt.operation_kind is not PendingOperationKind.RETIRE:
        raise OwnershipError("retire approval receipt required")
    if len(receipt.object_ids_versions) != 1:
        raise OwnershipError("retire receipt must bind one object")
    knowledge_id, version = receipt.object_ids_versions[0]
    record = backend.retire(knowledge_id, version, receipt.operation_id)
    if record.status is not KnowledgeStatus.RETIRED:
        raise OwnershipError("backend did not retire approved object")
    return record


def plan_uninstall(
    choice: UninstallDataChoice, deletion_plan: DeletionPlan | None
) -> UninstallPlan:
    if choice is UninstallDataChoice.DELETE and deletion_plan is None:
        raise OwnershipError("delete uninstall choice requires an approved deletion plan")
    if choice is UninstallDataChoice.KEEP and deletion_plan is not None:
        raise OwnershipError("keep uninstall choice cannot include deletion")
    return UninstallPlan(choice, True, True, deletion_plan)
