<!-- Updated: 2026-09-21 | Based on commit: 4213d8b -->

# expertiseOS

expertiseOS is a local-first learning companion for supported Codex and Claude Code environments. It helps an individual retain approved knowledge from AI-assisted work, revisit it later, and build evidence of independent understanding without taking control of the underlying task.

## Project status

This repository currently contains the MVP product specification and implementation plan. Application code has not been started.

## Core principles

- The user explicitly approves every substantive knowledge write.
- Unapproved candidate content remains volatile and is never persisted.
- Codex and Claude Code share one local repository and behavioral contract.
- Learning support is optional and must not block authorized work.
- Knowledge, user consent, provenance, and mastery are separate concerns.

## Documentation

- [MVP Product Requirements Document](expertiseOS_MVP_PRD.md)
- [Implementation plan](expertiseOS_mvp_agent_plan/final_plan.md)
- [Scope and guardrails](expertiseOS_mvp_agent_plan/00_scope_and_guardrails.md)
- [Acceptance and end-to-end plan](expertiseOS_mvp_agent_plan/06_acceptance_and_e2e.md)
- [Requirement traceability matrix](expertiseOS_mvp_agent_plan/08_traceability_matrix.md)

## Planned implementation

The MVP is planned as a small local Python service with a shared state store, a Basic Memory backend adapter, and thin Codex and Claude Code host adapters. The first engineering gate validates host integration feasibility, approval capture, local-only storage and retrieval, and dependency licensing before implementation begins.
