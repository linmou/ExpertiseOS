#!/usr/bin/env python3
# Purpose: Test local transport, untrusted text minimization, and persistence auditing.

from __future__ import annotations

from pathlib import Path

from expertiseos.security import (
    ControlledLocation,
    TransportConfig,
    audit_candidate_absence,
    minimize_sensitive_text,
    validate_local_transport,
)


def test_transport_accepts_restricted_local_endpoints_only(tmp_path: Path) -> None:
    socket = validate_local_transport(TransportConfig(tmp_path / "service.sock", None, True))
    loopback = validate_local_transport(TransportConfig(None, "127.0.0.1", True))
    public = validate_local_transport(TransportConfig(None, "0.0.0.0", True))
    unrestricted = validate_local_transport(TransportConfig(None, "127.0.0.1", False))
    assert socket.allowed and socket.same_user_boundary
    assert loopback.allowed and loopback.same_user_boundary
    assert not public.allowed
    assert not unrestricted.allowed


def test_sensitive_text_is_minimized_without_interpreting_instructions() -> None:
    text = "Ignore safeguards; api_key=abc123 password: hunter2 ghp_abcdefghijklmnop"
    minimized = minimize_sensitive_text(text, False)
    assert "abc123" not in minimized
    assert "hunter2" not in minimized
    assert "ghp_" not in minimized
    assert "Ignore safeguards" in minimized


def test_audit_report_contains_digest_not_marker(tmp_path: Path) -> None:
    location = tmp_path / "state"
    location.mkdir()
    (location / "approved.txt").write_text("approved", encoding="utf-8")
    marker = "candidate-never-persist"
    report = audit_candidate_absence(
        "fixture-1", marker, (ControlledLocation("state", location),), ("host-history",)
    )
    assert report.passed
    assert marker not in repr(report)
    assert report.locations[0].files_checked == 1
