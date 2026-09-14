# Feasibility Bootstrap Development Guidelines

**Intent**: Keep implementation of component 001 aligned with its minimal Python contracts and verification gates.

Auto-generated from all feature plans. Last updated: 2026-09-14

## Active Technologies

- Python 3.12 + Python standard library for contracts/fakes; pytest for verification; exact supported Codex, Claude Code, Basic Memory, and host integration versions selected and pinned by G0 evidence (001-feasibility-bootstrap)

## Project Structure

```text
src/
tests/
```

## Commands

Use the format, lint, mypy, import, unit, and integration commands defined in `pyproject.toml` after T001 creates them. Do not invent alternate command paths.

## Code Style

Python 3.12: Follow standard conventions

Every value-object field is required at construction. Do not add dataclass defaults.

## Scope

This component owns G0 feasibility evidence, minimal package bootstrap, the shared host/backend contracts, and deterministic fakes. It does not implement consent, production adapters, production backend mapping, learning, export, or product integration.

## Recent Changes

- 001-feasibility-bootstrap: Added Python 3.12 + Python standard library for contracts/fakes; pytest for verification; exact supported Codex, Claude Code, Basic Memory, and host integration versions selected and pinned by G0 evidence

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
