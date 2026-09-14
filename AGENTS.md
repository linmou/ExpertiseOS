# Consent Core Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-09-14

## Active Technologies

- Python 3.12 + Python standard library plus the model/validation choice and narrow `HostAdapter`/`KnowledgeBackend` contracts delivered by C001 (002-consent-core)

## Project Structure

```text
src/
tests/
```

## Commands

Use the test, mypy, and lint commands defined by the integrated C001 bootstrap. Run
focused consent-core tests before the repository-wide suite.

## Code Style

Python 3.12: follow standard conventions. Dataclass definitions must not provide
field defaults; supply every field explicitly at construction sites.

## Recent Changes

- 002-consent-core: Added Python 3.12 + Python standard library plus the model/validation choice and narrow `HostAdapter`/`KnowledgeBackend` contracts delivered by C001

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
