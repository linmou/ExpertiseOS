#!/usr/bin/env python3
# Purpose: Provide deterministic HostAdapter and KnowledgeBackend fakes for downstream tests.

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import datetime, timedelta
from typing import TypeVar, cast

from expertiseos.hosts.contract import (
    DecisionBinding,
    DecisionObservation,
    DecisionRejection,
    EventKind,
    HostAdapter,
    HostCapability,
    HostContractError,
    HostEvent,
)
from expertiseos.knowledge.backend import (
    ApprovedKnowledgeInput,
    BackendHealth,
    DeleteResult,
    IdempotencyConflictError,
    IndexState,
    KnowledgeBackend,
    KnowledgeRecord,
    KnowledgeStatus,
    RebuildResult,
    RelationshipInput,
    SearchMode,
    SearchQuery,
    SearchResult,
    StoreState,
    VersionConflictError,
)

T = TypeVar("T")


class DeterministicClock:
    def __init__(self, current: datetime, step: timedelta) -> None:
        self._current = current
        self._step = step

    def __call__(self) -> datetime:
        result = self._current
        self._current += self._step
        return result


class DeterministicIdGenerator:
    def __init__(self, prefix: str, next_value: int) -> None:
        self._prefix = prefix
        self._next_value = next_value

    def __call__(self) -> str:
        result = f"{self._prefix}-{self._next_value}"
        self._next_value += 1
        return result


class FakeHostAdapter(HostAdapter):
    def __init__(
        self,
        adapter_id: str,
        session_id: str,
        capabilities: tuple[HostCapability, ...],
    ) -> None:
        self._adapter_id = adapter_id
        self._session_id = session_id
        self._capabilities = capabilities
        self._events: list[HostEvent] = []
        self._atomic_depth = 0
        self._started = False
        self._ended = False
        self._observed_user_events: set[str] = set()

    @property
    def adapter_id(self) -> str:
        return self._adapter_id

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def events(self) -> tuple[HostEvent, ...]:
        return tuple(self._events)

    @property
    def checkpoint_eligible(self) -> bool:
        return self._started and not self._ended and self._atomic_depth == 0

    def capabilities(self) -> tuple[HostCapability, ...]:
        return self._capabilities

    def _accept(self, event: HostEvent, expected_kind: EventKind) -> None:
        if event.adapter_id != self.adapter_id or event.session_id != self.session_id:
            raise HostContractError("event is outside adapter session")
        if event.kind is not expected_kind:
            raise HostContractError(f"expected {expected_kind}, got {event.kind}")
        if self._ended:
            raise HostContractError("session already ended")

    def on_session_start(self, event: HostEvent) -> None:
        self._accept(event, EventKind.SESSION_START)
        if self._started:
            raise HostContractError("session already started")
        self._started = True
        self._events.append(event)

    def _accept_active(self, event: HostEvent, expected_kind: EventKind) -> None:
        self._accept(event, expected_kind)
        if not self._started:
            raise HostContractError("session has not started")

    def on_user_event(self, event: HostEvent) -> None:
        self._accept_active(event, EventKind.USER_INPUT)
        self._events.append(event)

    def on_atomic_begin(self, event: HostEvent) -> None:
        self._accept_active(event, EventKind.ATOMIC_BEGIN)
        self._atomic_depth += 1
        self._events.append(event)

    def on_atomic_end(self, event: HostEvent) -> None:
        self._accept_active(event, EventKind.ATOMIC_END)
        if self._atomic_depth == 0:
            raise HostContractError("atomic operation is not open")
        self._atomic_depth -= 1
        self._events.append(event)

    def on_checkpoint(self, event: HostEvent) -> None:
        self._accept_active(event, EventKind.CHECKPOINT)
        if self._atomic_depth:
            raise HostContractError("checkpoint is ineligible during atomic operation")
        self._events.append(event)

    def on_session_end(self, event: HostEvent) -> None:
        self._accept_active(event, EventKind.SESSION_END)
        if self._atomic_depth:
            raise HostContractError("session cannot end during atomic operation")
        self._ended = True
        self._events.append(event)

    def register_decision_if_unambiguous(
        self, event: HostEvent, binding: DecisionBinding
    ) -> DecisionObservation:
        rejection = self._decision_rejection(event, binding)
        if rejection is not DecisionRejection.NONE:
            return DecisionObservation(False, None, None, rejection)
        assert event.action is not None
        assert event.user_input_ref is not None
        self._observed_user_events.add(event.event_id)
        return DecisionObservation(True, event.action, event.user_input_ref, DecisionRejection.NONE)

    def _decision_rejection(self, event: HostEvent, binding: DecisionBinding) -> DecisionRejection:
        if self._ended:
            return DecisionRejection.SESSION_ENDED
        if event.kind is not EventKind.USER_INPUT:
            return DecisionRejection.NOT_USER_INPUT
        if not event.user_input_ref:
            return DecisionRejection.MISSING_USER_PROVENANCE
        if event.adapter_id != self.adapter_id or binding.adapter_id != self.adapter_id:
            return DecisionRejection.WRONG_ADAPTER
        if event.session_id != self.session_id or binding.session_id != self.session_id:
            return DecisionRejection.WRONG_SESSION
        if event.event_id in self._observed_user_events:
            return DecisionRejection.ALREADY_OBSERVED
        if event.action is None:
            return DecisionRejection.AMBIGUOUS_ACTION
        if event.action not in binding.allowed_actions:
            return DecisionRejection.ACTION_NOT_ALLOWED
        return DecisionRejection.NONE


class FakeKnowledgeBackend(KnowledgeBackend):
    def __init__(
        self,
        clock: Callable[[], datetime],
        id_generator: Callable[[], str],
        canonical_store: StoreState,
        index_state: IndexState,
        search_mode: SearchMode,
    ) -> None:
        self._clock = clock
        self._id_generator = id_generator
        self._canonical_store = canonical_store
        self._index_state = index_state
        self._search_mode = search_mode
        self._history: dict[str, list[KnowledgeRecord]] = {}
        self._operations: dict[str, tuple[object, object]] = {}

    def _run_operation(self, operation_id: str, command: object, action: Callable[[], T]) -> T:
        if not operation_id:
            raise ValueError("operation_id is required")
        prior = self._operations.get(operation_id)
        if prior is not None:
            prior_command, prior_result = prior
            if prior_command != command:
                raise IdempotencyConflictError("operation_id reused with different input")
            return cast(T, prior_result)
        result = action()
        self._operations[operation_id] = (command, result)
        return result

    def _current(self, knowledge_id: str) -> KnowledgeRecord:
        versions = self._history.get(knowledge_id)
        if not versions:
            raise KeyError(knowledge_id)
        return versions[-1]

    @staticmethod
    def _require_version(record: KnowledgeRecord, expected_version: int) -> None:
        if record.version != expected_version:
            raise VersionConflictError(
                f"expected version {expected_version}, current version {record.version}"
            )

    def create_approved(self, value: ApprovedKnowledgeInput, operation_id: str) -> KnowledgeRecord:
        if not isinstance(value, ApprovedKnowledgeInput):
            raise TypeError("fake backend accepts ApprovedKnowledgeInput only")

        def create() -> KnowledgeRecord:
            knowledge_id = self._id_generator()
            now = self._clock()
            record = KnowledgeRecord(
                knowledge_id,
                1,
                value.content,
                value.content_digest,
                value.categories,
                value.subjects,
                value.applicability_scope,
                value.evidential_status,
                value.source_refs,
                value.contribution_origin,
                KnowledgeStatus.ACTIVE,
                (),
                now,
                now,
            )
            self._history[knowledge_id] = [record]
            return record

        return self._run_operation(operation_id, ("create", value), create)

    def get(
        self,
        knowledge_id: str,
        version: int | None = None,
        include_retired: bool = False,
    ) -> KnowledgeRecord | None:
        versions = self._history.get(knowledge_id)
        if not versions:
            return None
        record = (
            versions[-1]
            if version is None
            else next((item for item in versions if item.version == version), None)
        )
        if record is None or (record.status is KnowledgeStatus.RETIRED and not include_retired):
            return None
        return record

    def get_current_versions(self, knowledge_ids: tuple[str, ...]) -> Mapping[str, int]:
        return {
            knowledge_id: self._history[knowledge_id][-1].version
            for knowledge_id in knowledge_ids
            if knowledge_id in self._history
        }

    def search(self, query: SearchQuery) -> tuple[SearchResult, ...]:
        if self._canonical_store is StoreState.UNAVAILABLE:
            return ()
        matches: list[SearchResult] = []
        needle = query.text.casefold()
        for knowledge_id in sorted(self._history):
            record = self._history[knowledge_id][-1]
            if record.status is KnowledgeStatus.RETIRED:
                continue
            if query.scope is not None and record.applicability_scope != query.scope:
                continue
            if needle not in record.content.casefold():
                continue
            matches.append(
                SearchResult(
                    record.id,
                    record.version,
                    record.content[:240],
                    record.source_refs,
                    record.relationships,
                    (),
                    self._search_mode,
                    self._index_state,
                )
            )
            if len(matches) == query.limit:
                break
        return tuple(matches)

    def update_approved(
        self,
        knowledge_id: str,
        expected_version: int,
        value: ApprovedKnowledgeInput,
        operation_id: str,
    ) -> KnowledgeRecord:
        if not isinstance(value, ApprovedKnowledgeInput):
            raise TypeError("fake backend accepts ApprovedKnowledgeInput only")
        command = ("update", knowledge_id, expected_version, value)

        def update() -> KnowledgeRecord:
            current = self._current(knowledge_id)
            self._require_version(current, expected_version)
            record = KnowledgeRecord(
                current.id,
                current.version + 1,
                value.content,
                value.content_digest,
                value.categories,
                value.subjects,
                value.applicability_scope,
                value.evidential_status,
                value.source_refs,
                value.contribution_origin,
                KnowledgeStatus.ACTIVE,
                current.relationships,
                current.created_at,
                self._clock(),
            )
            self._history[knowledge_id].append(record)
            return record

        return self._run_operation(operation_id, command, update)

    def set_relationships(
        self,
        relationships: tuple[RelationshipInput, ...],
        expected_versions: Mapping[str, int],
        operation_id: str,
    ) -> tuple[KnowledgeRecord, ...]:
        normalized_versions = tuple(sorted(expected_versions.items()))
        command = ("relationships", relationships, normalized_versions)

        def set_values() -> tuple[KnowledgeRecord, ...]:
            for knowledge_id, expected_version in normalized_versions:
                self._require_version(self._current(knowledge_id), expected_version)
            for relationship in relationships:
                if self.get(relationship.source_id, relationship.source_version, True) is None:
                    raise KeyError(relationship.source_id)
                if self.get(relationship.target_id, relationship.target_version, True) is None:
                    raise KeyError(relationship.target_id)
            results: list[KnowledgeRecord] = []
            source_ids = sorted({relationship.source_id for relationship in relationships})
            for source_id in source_ids:
                current = self._current(source_id)
                selected = tuple(r for r in relationships if r.source_id == source_id)
                updated = replace(
                    current,
                    version=current.version + 1,
                    relationships=selected,
                    updated_at=self._clock(),
                )
                self._history[source_id].append(updated)
                results.append(updated)
            return tuple(results)

        return self._run_operation(operation_id, command, set_values)

    def retire(
        self, knowledge_id: str, expected_version: int, operation_id: str
    ) -> KnowledgeRecord:
        command = ("retire", knowledge_id, expected_version)

        def retire_value() -> KnowledgeRecord:
            current = self._current(knowledge_id)
            self._require_version(current, expected_version)
            retired = replace(
                current,
                version=current.version + 1,
                status=KnowledgeStatus.RETIRED,
                updated_at=self._clock(),
            )
            self._history[knowledge_id].append(retired)
            return retired

        return self._run_operation(operation_id, command, retire_value)

    def delete(self, knowledge_id: str, expected_version: int, operation_id: str) -> DeleteResult:
        command = ("delete", knowledge_id, expected_version)

        def delete_value() -> DeleteResult:
            current = self._current(knowledge_id)
            self._require_version(current, expected_version)
            deleted = DeleteResult(knowledge_id, len(self._history[knowledge_id]))
            del self._history[knowledge_id]
            return deleted

        return self._run_operation(operation_id, command, delete_value)

    def rebuild_index(self) -> RebuildResult:
        self._index_state = IndexState.READY
        indexed = sum(
            versions[-1].status is KnowledgeStatus.ACTIVE for versions in self._history.values()
        )
        return RebuildResult(indexed, self._index_state)

    def health(self) -> BackendHealth:
        return BackendHealth(
            self._canonical_store,
            self._index_state,
            self._search_mode,
            (),
        )
