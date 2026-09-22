#!/usr/bin/env python3
# Purpose: Enforce local transport, sensitive-text minimization, and persistence audits.

from __future__ import annotations

import hashlib
import ipaddress
import re
from dataclasses import dataclass
from pathlib import Path


class SecurityBoundaryError(ValueError):
    """Raised when local security boundary input is unsafe."""


@dataclass(frozen=True)
class TransportConfig:
    unix_socket: Path | None
    bind_host: str | None
    restrict_local_user: bool


@dataclass(frozen=True)
class TransportValidation:
    allowed: bool
    same_user_boundary: bool
    reason: str


@dataclass(frozen=True)
class ControlledLocation:
    name: str
    path: Path


@dataclass(frozen=True)
class LocationAudit:
    name: str
    path: str
    marker_found: bool
    files_checked: int


@dataclass(frozen=True)
class PersistenceAuditReport:
    fixture_id: str
    marker_digest: str
    locations: tuple[LocationAudit, ...]
    excluded_locations: tuple[str, ...]
    passed: bool


_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_-]{12,}\b"),
)


def validate_local_transport(config: TransportConfig) -> TransportValidation:
    if config.unix_socket is not None:
        if not config.unix_socket.is_absolute():
            return TransportValidation(False, False, "unix_socket_must_be_absolute")
        return TransportValidation(True, config.restrict_local_user, "local_socket")
    if config.bind_host is None:
        return TransportValidation(False, False, "transport_not_configured")
    try:
        address = ipaddress.ip_address(config.bind_host)
    except ValueError:
        return TransportValidation(False, False, "numeric_loopback_required")
    if not address.is_loopback:
        return TransportValidation(False, False, "public_bind_rejected")
    if not config.restrict_local_user:
        return TransportValidation(False, False, "local_user_restriction_required")
    return TransportValidation(True, True, "loopback_restricted")


def minimize_sensitive_text(text: str, allow_sensitive: bool) -> str:
    if allow_sensitive:
        return text
    minimized = text
    for pattern in _SECRET_PATTERNS:
        minimized = pattern.sub(
            lambda match: f"{match.group(1)}=[REDACTED]" if match.lastindex == 2 else "[REDACTED]",
            minimized,
        )
    return minimized


def _files(location: Path) -> tuple[Path, ...]:
    if not location.exists():
        return ()
    if location.is_file():
        return (location,)
    return tuple(path for path in sorted(location.rglob("*")) if path.is_file())


def audit_candidate_absence(
    fixture_id: str,
    marker: str,
    locations: tuple[ControlledLocation, ...],
    excluded_locations: tuple[str, ...],
) -> PersistenceAuditReport:
    if not fixture_id or not marker:
        raise SecurityBoundaryError("fixture id and marker are required")
    marker_bytes = marker.encode("utf-8")
    audits: list[LocationAudit] = []
    for location in locations:
        found = False
        files = _files(location.path)
        for path in files:
            try:
                if marker_bytes in path.read_bytes():
                    found = True
                    break
            except OSError as error:
                raise SecurityBoundaryError(
                    f"cannot inspect controlled location {location.name}"
                ) from error
        audits.append(LocationAudit(location.name, str(location.path), found, len(files)))
    return PersistenceAuditReport(
        fixture_id,
        hashlib.sha256(marker_bytes).hexdigest(),
        tuple(audits),
        excluded_locations,
        all(not item.marker_found for item in audits),
    )
