#!/usr/bin/env python3
# Purpose: Map approved expertiseOS knowledge to Basic Memory 0.23.2 public local CLI notes.

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from expertiseos.knowledge.backend import (
    ApprovedKnowledgeInput,
    BackendHealth,
    DeleteResult,
    IdempotencyConflictError,
    IndexState,
    KnowledgeRecord,
    KnowledgeStatus,
    RebuildResult,
    RelationshipInput,
    SearchMode,
    SearchQuery,
    SearchResult,
    StoreState,
    TrustLevel,
    VersionConflictError,
)

CliRunner = Callable[[Path, tuple[str, ...], Mapping[str, str]], str]
_TOKEN = re.compile(r"[A-Za-z0-9_]{2,}")
_MARKER_PREFIX = "<!-- expertiseos:"
_MARKER_SUFFIX = " -->"


class BackendUnavailableError(RuntimeError):
    """Raised when canonical Basic Memory operations cannot complete."""


def subprocess_cli_runner(timeout_seconds: float) -> CliRunner:
    """Create a runner for Basic Memory's supported local CLI."""

    def run(binary: Path, arguments: tuple[str, ...], environment: Mapping[str, str]) -> str:
        try:
            completed = subprocess.run(
                (str(binary), *arguments),
                check=True,
                capture_output=True,
                text=True,
                env=dict(environment),
                timeout=timeout_seconds,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise BackendUnavailableError("Basic Memory command failed") from error
        return completed.stdout

    return run


class BasicMemoryBackend:
    """Persist approved versions through Basic Memory and content-free local mapping state."""

    def __init__(
        self,
        binary: Path,
        project: str,
        config_dir: Path,
        home: Path,
        state_path: Path,
        clock: Callable[[], datetime],
        command_runner: CliRunner,
    ) -> None:
        self._binary = binary
        self._project = project
        self._config_dir = config_dir
        self._home = home
        self._state_path = state_path
        self._clock = clock
        self._command_runner = command_runner
        self._command_log: list[tuple[str, ...]] = []
        self._canonical_state = StoreState.READY
        self._index_state = IndexState.READY
        self._search_mode = SearchMode.LOCAL_INDEXED
        self._details: list[str] = []
        self._state = self._load_state()

    @property
    def command_log(self) -> tuple[tuple[str, ...], ...]:
        return tuple(self._command_log)

    def _environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        environment.update(
            {
                "BASIC_MEMORY_CONFIG_DIR": str(self._config_dir),
                "BASIC_MEMORY_HOME": str(self._home),
                "BASIC_MEMORY_AUTO_UPDATE": "false",
                "BASIC_MEMORY_SEMANTIC_SEARCH_ENABLED": "false",
            }
        )
        return environment

    def _run_cli(self, *arguments: str) -> str:
        command = tuple(arguments)
        self._command_log.append(command)
        return self._command_runner(self._binary, command, self._environment())

    def _load_state(self) -> dict[str, Any]:
        if not self._state_path.exists():
            return {"schema": 1, "records": {}, "operations": {}, "tokens": {}}
        try:
            loaded = cast(object, json.loads(self._state_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as error:
            self._canonical_state = StoreState.UNAVAILABLE
            raise BackendUnavailableError("backend mapping state is unreadable") from error
        if (
            not isinstance(loaded, dict)
            or loaded.get("schema") != 1
            or not isinstance(loaded.get("records"), dict)
            or not isinstance(loaded.get("operations"), dict)
            or not isinstance(loaded.get("tokens"), dict)
        ):
            self._canonical_state = StoreState.UNAVAILABLE
            raise BackendUnavailableError("backend mapping state has an unsupported schema")
        return cast(dict[str, Any], loaded)

    def _save_state(self) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._state_path.with_suffix(f"{self._state_path.suffix}.tmp")
        payload = json.dumps(self._state, indent=2, sort_keys=True)
        try:
            temporary.write_text(payload, encoding="utf-8")
            os.replace(temporary, self._state_path)
        except OSError as error:
            self._canonical_state = StoreState.UNAVAILABLE
            raise BackendUnavailableError("backend mapping state could not be saved") from error

    def _records(self) -> dict[str, dict[str, Any]]:
        return cast(dict[str, dict[str, Any]], self._state["records"])

    def _operations(self) -> dict[str, dict[str, Any]]:
        return cast(dict[str, dict[str, Any]], self._state["operations"])

    def _tokens(self) -> dict[str, list[str]]:
        return cast(dict[str, list[str]], self._state["tokens"])

    @staticmethod
    def _knowledge_id(operation_id: str) -> str:
        digest = hashlib.sha256(operation_id.encode("utf-8")).hexdigest()[:24]
        return f"knowledge-{digest}"

    @staticmethod
    def _identifier(knowledge_id: str, version: int) -> str:
        return f"expertiseos/{knowledge_id}-v{version}"

    @staticmethod
    def _value_document(value: ApprovedKnowledgeInput) -> dict[str, object]:
        return {
            "content": value.content,
            "content_digest": value.content_digest,
            "categories": list(value.categories),
            "subjects": list(value.subjects),
            "applicability_scope": value.applicability_scope,
            "evidential_status": value.evidential_status,
            "source_refs": list(value.source_refs),
            "contribution_origin": value.contribution_origin,
        }

    @staticmethod
    def _relationship_document(value: RelationshipInput) -> dict[str, object]:
        return {
            "source_id": value.source_id,
            "source_version": value.source_version,
            "target_id": value.target_id,
            "target_version": value.target_version,
            "type": value.type,
            "explanation": value.explanation,
            "source_ref": value.source_ref,
        }

    @staticmethod
    def _digest(document: object) -> str:
        encoded = json.dumps(document, separators=(",", ":"), sort_keys=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _replayed(self, operation_id: str, digest: str) -> dict[str, Any] | None:
        if not operation_id:
            raise ValueError("operation_id is required")
        prior = self._operations().get(operation_id)
        if prior is None:
            return None
        if prior["digest"] != digest:
            raise IdempotencyConflictError("operation_id reused with different semantic input")
        return prior

    def _store_operation(
        self,
        operation_id: str,
        digest: str,
        kind: str,
        refs: tuple[tuple[str, int], ...],
        deleted_versions: int | None,
    ) -> None:
        self._operations()[operation_id] = {
            "digest": digest,
            "kind": kind,
            "refs": [[knowledge_id, version] for knowledge_id, version in refs],
            "deleted_versions": deleted_versions,
        }

    @staticmethod
    def _metadata(record: KnowledgeRecord, operation_id: str) -> dict[str, object]:
        return {
            "schema": 1,
            "id": record.id,
            "version": record.version,
            "content_length": len(record.content),
            "content_digest": record.content_digest,
            "categories": list(record.categories),
            "subjects": list(record.subjects),
            "applicability_scope": record.applicability_scope,
            "evidential_status": record.evidential_status,
            "source_refs": list(record.source_refs),
            "contribution_origin": record.contribution_origin,
            "status": record.status.value,
            "relationships": [
                BasicMemoryBackend._relationship_document(value) for value in record.relationships
            ],
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "operation_id": operation_id,
        }

    @staticmethod
    def _note(record: KnowledgeRecord, operation_id: str) -> str:
        metadata = BasicMemoryBackend._metadata(record, operation_id)
        encoded = base64.urlsafe_b64encode(
            json.dumps(metadata, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ).decode("ascii")
        relation_lines = "".join(
            f"\n- {value.type} [[{value.target_id}-v{value.target_version}]]"
            for value in record.relationships
        )
        relations = "" if not relation_lines else f"\n\n## Relations{relation_lines}"
        return f"{_MARKER_PREFIX}{encoded}{_MARKER_SUFFIX}\n{record.content}{relations}"

    @staticmethod
    def _parse_note(content: str) -> KnowledgeRecord:
        marker_start = content.find(_MARKER_PREFIX)
        if marker_start < 0 or content[:marker_start].strip():
            raise BackendUnavailableError("Basic Memory note lacks expertiseOS metadata")
        marker, separator, remainder = content[marker_start:].partition("\n")
        if (
            not separator
            or not marker.startswith(_MARKER_PREFIX)
            or not marker.endswith(_MARKER_SUFFIX)
        ):
            raise BackendUnavailableError("Basic Memory note lacks expertiseOS metadata")
        encoded = marker[len(_MARKER_PREFIX) : -len(_MARKER_SUFFIX)]
        try:
            metadata = cast(
                dict[str, Any],
                json.loads(base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8")),
            )
            content_length = int(metadata["content_length"])
            approved_content = remainder[:content_length]
            relationships = tuple(
                RelationshipInput(
                    str(item["source_id"]),
                    int(item["source_version"]),
                    str(item["target_id"]),
                    int(item["target_version"]),
                    str(item["type"]),
                    None if item["explanation"] is None else str(item["explanation"]),
                    None if item["source_ref"] is None else str(item["source_ref"]),
                )
                for item in cast(list[dict[str, Any]], metadata["relationships"])
            )
            record = KnowledgeRecord(
                str(metadata["id"]),
                int(metadata["version"]),
                approved_content,
                str(metadata["content_digest"]),
                tuple(str(value) for value in cast(list[object], metadata["categories"])),
                tuple(str(value) for value in cast(list[object], metadata["subjects"])),
                None
                if metadata["applicability_scope"] is None
                else str(metadata["applicability_scope"]),
                None
                if metadata["evidential_status"] is None
                else str(metadata["evidential_status"]),
                tuple(str(value) for value in cast(list[object], metadata["source_refs"])),
                str(metadata["contribution_origin"]),
                KnowledgeStatus(str(metadata["status"])),
                relationships,
                datetime.fromisoformat(str(metadata["created_at"])),
                datetime.fromisoformat(str(metadata["updated_at"])),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise BackendUnavailableError("Basic Memory note metadata is invalid") from error
        if hashlib.sha256(record.content.encode("utf-8")).hexdigest() != record.content_digest:
            raise BackendUnavailableError("Basic Memory note content digest does not match")
        return record

    def _read_identifier(self, identifier: str) -> KnowledgeRecord | None:
        output = self._run_cli(
            "tool",
            "read-note",
            identifier,
            "--project",
            self._project,
            "--json",
            "--local",
        )
        payload = cast(dict[str, Any], json.loads(output))
        content = payload.get("content")
        if content is None:
            return None
        if not isinstance(content, str):
            raise BackendUnavailableError("Basic Memory read returned invalid content")
        return self._parse_note(content)

    def _write_record(self, record: KnowledgeRecord, operation_id: str) -> None:
        identifier = self._identifier(record.id, record.version)
        try:
            self._run_cli(
                "tool",
                "write-note",
                "--title",
                f"{record.id}-v{record.version}",
                "--folder",
                "expertiseos",
                "--content",
                self._note(record, operation_id),
                "--type",
                "expertiseos-knowledge",
                "--project",
                self._project,
                "--overwrite",
                "--local",
            )
        except Exception as write_error:
            try:
                reconciled = self._read_identifier(identifier)
            except Exception as read_error:
                self._canonical_state = StoreState.UNAVAILABLE
                raise BackendUnavailableError(
                    "Basic Memory write could not be reconciled"
                ) from read_error
            if reconciled != record:
                self._canonical_state = StoreState.UNAVAILABLE
                raise BackendUnavailableError(
                    "Basic Memory canonical write failed"
                ) from write_error
            self._index_state = IndexState.DEGRADED
            self._search_mode = SearchMode.KEYWORD
            self._details.append("write acknowledgement failed; canonical note reconciled")

    @staticmethod
    def _token_hashes(content: str) -> set[str]:
        return {
            hashlib.sha256(token.casefold().encode("utf-8")).hexdigest()
            for token in _TOKEN.findall(content)
        }

    def _replace_tokens(self, record: KnowledgeRecord | None, knowledge_id: str) -> None:
        tokens = self._tokens()
        for token_hash in tuple(tokens):
            values = [value for value in tokens[token_hash] if value != knowledge_id]
            if values:
                tokens[token_hash] = values
            else:
                del tokens[token_hash]
        if record is None or record.status is KnowledgeStatus.RETIRED:
            return
        for token_hash in self._token_hashes(record.content):
            tokens.setdefault(token_hash, []).append(record.id)
            tokens[token_hash].sort()

    def _record_mapping(self, record: KnowledgeRecord) -> None:
        entry = self._records().setdefault(record.id, {"current": record.version, "versions": {}})
        entry["current"] = record.version
        versions = cast(dict[str, str], entry["versions"])
        versions[str(record.version)] = self._identifier(record.id, record.version)
        self._replace_tokens(record, record.id)

    def _current(self, knowledge_id: str) -> KnowledgeRecord:
        record = self.get(knowledge_id, None, True)
        if record is None:
            raise KeyError(knowledge_id)
        return record

    @staticmethod
    def _require_version(record: KnowledgeRecord, expected_version: int) -> None:
        if record.version != expected_version:
            raise VersionConflictError(
                f"expected version {expected_version}, current version {record.version}"
            )

    def _records_from_replay(self, replay: Mapping[str, Any]) -> tuple[KnowledgeRecord, ...]:
        result: list[KnowledgeRecord] = []
        for knowledge_id, version in cast(list[list[object]], replay["refs"]):
            if not isinstance(knowledge_id, str) or not isinstance(version, int):
                raise BackendUnavailableError("operation replay reference is invalid")
            record = self.get(knowledge_id, version, True)
            if record is None:
                raise BackendUnavailableError("replayed canonical version is unavailable")
            result.append(record)
        return tuple(result)

    def create_approved(self, value: ApprovedKnowledgeInput, operation_id: str) -> KnowledgeRecord:
        if not isinstance(value, ApprovedKnowledgeInput):
            raise TypeError("Basic Memory backend accepts ApprovedKnowledgeInput only")
        document = {"kind": "create", "value": self._value_document(value)}
        digest = self._digest(document)
        replay = self._replayed(operation_id, digest)
        if replay is not None:
            return self._records_from_replay(replay)[0]
        knowledge_id = self._knowledge_id(operation_id)
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
        existing = self._read_identifier(self._identifier(knowledge_id, 1))
        if existing is not None and existing != record:
            raise IdempotencyConflictError("operation_id maps to different canonical input")
        if existing is None:
            self._write_record(record, operation_id)
        self._record_mapping(record)
        self._store_operation(operation_id, digest, "create", ((record.id, 1),), None)
        self._save_state()
        return record

    def get(
        self,
        knowledge_id: str,
        version: int | None = None,
        include_retired: bool = False,
    ) -> KnowledgeRecord | None:
        entry = self._records().get(knowledge_id)
        if entry is None:
            return None
        selected = int(entry["current"]) if version is None else version
        identifier = cast(dict[str, str], entry["versions"]).get(str(selected))
        if identifier is None:
            return None
        try:
            record = self._read_identifier(identifier)
        except Exception as error:
            self._canonical_state = StoreState.UNAVAILABLE
            raise BackendUnavailableError("Basic Memory canonical read failed") from error
        if record is None:
            self._canonical_state = StoreState.UNAVAILABLE
            raise BackendUnavailableError("mapped Basic Memory note is missing")
        self._canonical_state = StoreState.READY
        if record.status is KnowledgeStatus.RETIRED and not include_retired:
            return None
        return record

    def get_current_versions(self, knowledge_ids: tuple[str, ...]) -> Mapping[str, int]:
        return {
            knowledge_id: int(self._records()[knowledge_id]["current"])
            for knowledge_id in knowledge_ids
            if knowledge_id in self._records()
        }

    def update_approved(
        self,
        knowledge_id: str,
        expected_version: int,
        value: ApprovedKnowledgeInput,
        operation_id: str,
    ) -> KnowledgeRecord:
        if not isinstance(value, ApprovedKnowledgeInput):
            raise TypeError("Basic Memory backend accepts ApprovedKnowledgeInput only")
        document = {
            "kind": "update",
            "knowledge_id": knowledge_id,
            "expected_version": expected_version,
            "value": self._value_document(value),
        }
        digest = self._digest(document)
        replay = self._replayed(operation_id, digest)
        if replay is not None:
            return self._records_from_replay(replay)[0]
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
        self._write_record(record, operation_id)
        self._record_mapping(record)
        self._store_operation(operation_id, digest, "update", ((record.id, record.version),), None)
        self._save_state()
        return record

    def set_relationships(
        self,
        relationships: tuple[RelationshipInput, ...],
        expected_versions: Mapping[str, int],
        operation_id: str,
    ) -> tuple[KnowledgeRecord, ...]:
        normalized_versions = tuple(sorted(expected_versions.items()))
        document = {
            "kind": "relationships",
            "relationships": [self._relationship_document(value) for value in relationships],
            "expected_versions": normalized_versions,
        }
        digest = self._digest(document)
        replay = self._replayed(operation_id, digest)
        if replay is not None:
            return self._records_from_replay(replay)
        for knowledge_id, expected_version in normalized_versions:
            self._require_version(self._current(knowledge_id), expected_version)
        for relationship in relationships:
            if self.get(relationship.source_id, relationship.source_version, True) is None:
                raise KeyError(relationship.source_id)
            if self.get(relationship.target_id, relationship.target_version, True) is None:
                raise KeyError(relationship.target_id)
        records: list[KnowledgeRecord] = []
        for source_id in sorted({value.source_id for value in relationships}):
            current = self._current(source_id)
            selected = tuple(value for value in relationships if value.source_id == source_id)
            record = KnowledgeRecord(
                current.id,
                current.version + 1,
                current.content,
                current.content_digest,
                current.categories,
                current.subjects,
                current.applicability_scope,
                current.evidential_status,
                current.source_refs,
                current.contribution_origin,
                current.status,
                selected,
                current.created_at,
                self._clock(),
            )
            self._write_record(record, operation_id)
            self._record_mapping(record)
            records.append(record)
        refs = tuple((record.id, record.version) for record in records)
        self._store_operation(operation_id, digest, "relationships", refs, None)
        self._save_state()
        return tuple(records)

    def retire(
        self, knowledge_id: str, expected_version: int, operation_id: str
    ) -> KnowledgeRecord:
        document = {
            "kind": "retire",
            "knowledge_id": knowledge_id,
            "expected_version": expected_version,
        }
        digest = self._digest(document)
        replay = self._replayed(operation_id, digest)
        if replay is not None:
            return self._records_from_replay(replay)[0]
        current = self._current(knowledge_id)
        self._require_version(current, expected_version)
        record = KnowledgeRecord(
            current.id,
            current.version + 1,
            current.content,
            current.content_digest,
            current.categories,
            current.subjects,
            current.applicability_scope,
            current.evidential_status,
            current.source_refs,
            current.contribution_origin,
            KnowledgeStatus.RETIRED,
            current.relationships,
            current.created_at,
            self._clock(),
        )
        self._write_record(record, operation_id)
        self._record_mapping(record)
        self._store_operation(operation_id, digest, "retire", ((record.id, record.version),), None)
        self._save_state()
        return record

    def delete(self, knowledge_id: str, expected_version: int, operation_id: str) -> DeleteResult:
        document = {
            "kind": "delete",
            "knowledge_id": knowledge_id,
            "expected_version": expected_version,
        }
        digest = self._digest(document)
        replay = self._replayed(operation_id, digest)
        if replay is not None:
            return DeleteResult(knowledge_id, int(replay["deleted_versions"]))
        current = self._current(knowledge_id)
        self._require_version(current, expected_version)
        entry = self._records()[knowledge_id]
        versions = cast(dict[str, str], entry["versions"])
        for identifier in versions.values():
            self._run_cli(
                "tool",
                "delete-note",
                identifier,
                "--project",
                self._project,
                "--local",
            )
        deleted_versions = len(versions)
        self._replace_tokens(None, knowledge_id)
        del self._records()[knowledge_id]
        self._store_operation(operation_id, digest, "delete", (), deleted_versions)
        self._save_state()
        return DeleteResult(knowledge_id, deleted_versions)

    def _matches(self, record: KnowledgeRecord, query: SearchQuery) -> bool:
        if record.status is KnowledgeStatus.RETIRED:
            return False
        if query.scope is not None and record.applicability_scope != query.scope:
            return False
        if record.id in query.exclusions or record.applicability_scope in query.exclusions:
            return False
        if query.subjects and not set(query.subjects).intersection(record.subjects):
            return False
        if query.categories and not set(query.categories).intersection(record.categories):
            return False
        return query.text.casefold() in record.content.casefold()

    def _search_result(
        self, record: KnowledgeRecord, mode: SearchMode, index_state: IndexState
    ) -> SearchResult:
        conflicts = tuple(
            sorted(
                {
                    relationship.target_id
                    for relationship in record.relationships
                    if relationship.type == "contradicts"
                }
            )
        )
        return SearchResult(
            record.id,
            record.version,
            record.content[:240],
            record.categories,
            record.subjects,
            record.applicability_scope,
            record.evidential_status,
            record.source_refs,
            all(not value.startswith("unavailable:") for value in record.source_refs),
            record.relationships,
            conflicts,
            TrustLevel.UNTRUSTED_DATA,
            mode,
            index_state,
        )

    def _indexed_records(self, query: SearchQuery) -> tuple[KnowledgeRecord, ...]:
        page = 1
        page_size = min(20, query.limit * 4)
        records: list[KnowledgeRecord] = []
        seen: set[str] = set()
        while len(records) < query.limit:
            output = self._run_cli(
                "tool",
                "search-notes",
                query.text,
                "--project",
                self._project,
                "--json",
                "--page",
                str(page),
                "--page-size",
                str(page_size),
                "--local",
            )
            payload = cast(dict[str, Any], json.loads(output))
            items = cast(list[dict[str, Any]], payload.get("results", []))
            for item in items:
                content = item.get("content")
                if not isinstance(content, str):
                    continue
                record = self._parse_note(content)
                current = self._records().get(record.id)
                if current is None or int(current["current"]) != record.version:
                    continue
                if record.id not in seen and self._matches(record, query):
                    seen.add(record.id)
                    records.append(record)
                if len(records) == query.limit:
                    break
            total = payload.get("total")
            if len(items) < page_size or (isinstance(total, int) and page * page_size >= total):
                break
            page += 1
        return tuple(records)

    def _keyword_records(self, query: SearchQuery) -> tuple[KnowledgeRecord, ...]:
        query_hashes = self._token_hashes(query.text)
        scores: dict[str, int] = {}
        for token_hash in query_hashes:
            for knowledge_id in self._tokens().get(token_hash, []):
                scores[knowledge_id] = scores.get(knowledge_id, 0) + 1
        records: list[KnowledgeRecord] = []
        for knowledge_id, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0])):
            record = self.get(knowledge_id, None, False)
            if record is not None and self._matches(record, query):
                records.append(record)
            if len(records) == query.limit:
                break
        return tuple(records)

    def search(self, query: SearchQuery) -> tuple[SearchResult, ...]:
        if self._canonical_state is StoreState.UNAVAILABLE:
            return ()
        try:
            records = self._indexed_records(query)
            mode = SearchMode.LOCAL_INDEXED
            index_state = IndexState.READY
            self._index_state = index_state
            self._search_mode = mode
        except Exception:
            self._index_state = IndexState.DEGRADED
            self._search_mode = SearchMode.KEYWORD
            self._details.append("indexed search failed; local keyword fallback used")
            mode = SearchMode.KEYWORD
            index_state = IndexState.DEGRADED
            try:
                records = self._keyword_records(query)
            except Exception:
                self._canonical_state = StoreState.UNAVAILABLE
                self._search_mode = SearchMode.UNAVAILABLE
                self._details.append("canonical read failed during keyword fallback")
                return ()
        return tuple(self._search_result(record, mode, index_state) for record in records)

    def rebuild_index(self) -> RebuildResult:
        active_records: list[KnowledgeRecord] = []
        for knowledge_id in sorted(self._records()):
            record = self.get(knowledge_id, None, True)
            if record is not None and record.status is KnowledgeStatus.ACTIVE:
                active_records.append(record)
        self._state["tokens"] = {}
        for record in active_records:
            self._replace_tokens(record, record.id)
        try:
            self._run_cli("reindex", "--search", "--project", self._project)
        except Exception as error:
            self._index_state = IndexState.UNAVAILABLE
            self._search_mode = SearchMode.KEYWORD
            self._details.append("Basic Memory search reindex failed")
            self._save_state()
            raise BackendUnavailableError("Basic Memory index rebuild failed") from error
        self._index_state = IndexState.READY
        self._search_mode = SearchMode.LOCAL_INDEXED
        self._save_state()
        return RebuildResult(len(active_records), self._index_state)

    def health(self) -> BackendHealth:
        return BackendHealth(
            self._canonical_state,
            self._index_state,
            self._search_mode,
            tuple(self._details),
        )
