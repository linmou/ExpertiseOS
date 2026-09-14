#!/usr/bin/env python3
# Purpose: Support tests for src/expertiseos/backends/basic_memory.py public CLI behavior.

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path

from expertiseos.backends.basic_memory import BasicMemoryBackend
from expertiseos.knowledge.backend import ApprovedKnowledgeInput
from tests.fakes import DeterministicClock


class FakeBasicMemoryCli:
    def __init__(self) -> None:
        self.notes: dict[str, str] = {}
        self.commands: list[tuple[str, ...]] = []
        self.fail_search = False
        self.fail_reindex = False
        self.fail_write_after_store = False

    @staticmethod
    def _option(arguments: tuple[str, ...], name: str) -> str:
        return arguments[arguments.index(name) + 1]

    def __call__(
        self, binary: Path, arguments: tuple[str, ...], environment: Mapping[str, str]
    ) -> str:
        assert binary.name == "basic-memory"
        assert environment["BASIC_MEMORY_SEMANTIC_SEARCH_ENABLED"] == "false"
        self.commands.append(arguments)
        if arguments[:2] == ("tool", "write-note"):
            title = self._option(arguments, "--title")
            folder = self._option(arguments, "--folder")
            content = self._option(arguments, "--content")
            identifier = f"{folder}/{title}"
            self.notes[identifier] = content
            if self.fail_write_after_store:
                self.fail_write_after_store = False
                raise RuntimeError("write acknowledgement failed")
            return json.dumps({"action": "created", "permalink": identifier})
        if arguments[:2] == ("tool", "read-note"):
            identifier = arguments[2]
            return json.dumps({"content": self.notes.get(identifier), "permalink": identifier})
        if arguments[:2] == ("tool", "search-notes"):
            if self.fail_search:
                raise RuntimeError("index unavailable")
            query = arguments[2].casefold()
            page = int(self._option(arguments, "--page"))
            page_size = int(self._option(arguments, "--page-size"))
            matches = [
                {"content": content, "permalink": identifier}
                for identifier, content in sorted(self.notes.items())
                if query in content.casefold()
            ]
            start = (page - 1) * page_size
            results = matches[start : start + page_size]
            return json.dumps({"results": results, "total": len(matches), "page_size": page_size})
        if arguments[:2] == ("tool", "delete-note"):
            identifier = arguments[2]
            existed = self.notes.pop(identifier, None) is not None
            return json.dumps({"deleted": existed})
        if arguments[:1] == ("reindex",):
            if self.fail_reindex:
                raise RuntimeError("reindex unavailable")
            return ""
        if arguments[:1] == ("status",):
            return json.dumps({"status": "ready"})
        raise AssertionError(f"unexpected Basic Memory command: {arguments}")


def approved(
    content: str,
    scope: str | None,
    categories: tuple[str, ...],
    subjects: tuple[str, ...],
    source_refs: tuple[str, ...],
) -> ApprovedKnowledgeInput:
    import hashlib

    return ApprovedKnowledgeInput(
        content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
        categories,
        subjects,
        scope,
        "observed",
        source_refs,
        "user",
    )


def backend(tmp_path: Path, cli: FakeBasicMemoryCli) -> BasicMemoryBackend:
    clock = DeterministicClock(datetime(2026, 9, 14, tzinfo=UTC), timedelta(seconds=1))
    return BasicMemoryBackend(
        Path("basic-memory"),
        "c003",
        tmp_path / "config",
        tmp_path / "home",
        tmp_path / "backend-state.json",
        clock,
        cli,
    )
