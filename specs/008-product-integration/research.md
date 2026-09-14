# Research: Product Integration and Acceptance

**Intent**: Record the few integration decisions needed to implement C008 without reopening upstream product semantics or adding infrastructure.

## Decision 1: One Thin Composition Facade

**Decision**: Expose promoted C002-C007 capabilities through one stateless `ExpertiseOSService` facade.

**Rationale**: A single host-neutral facade gives MCP and tests one stable entry point while leaving authorization, storage, retrieval, learning, controls, and ownership in their existing owners.

**Alternatives considered**:

- Register each upstream service directly with MCP: rejected because capability filtering and result/error shape would be duplicated.
- Add an orchestration or policy engine: rejected because no MVP requirement needs it and it would compete with existing domain state machines.

## Decision 2: Explicit, Narrow Tool Groups

**Decision**: Provide named operations for reads, proposals, proposal resolution, guarded commits, learner/control inspection and changes, ownership operations, and health; never expose backend methods.

**Rationale**: Explicit operations are inspectable and map directly to MVP requirements. They make it difficult to bypass the approval gate and avoid a generic command envelope.

**Alternatives considered**:

- One generic `execute_operation` tool: rejected because it obscures authorization and validation boundaries.
- Expose Basic Memory MCP writes: rejected because it bypasses exact approval binding.

## Decision 3: Markdown Shared Skill with Thin Host References

**Decision**: Keep all host-model behavior rules in one `skill/SKILL.md`; host packages reference it and adapters provide normalized facts.

**Rationale**: The product requires equivalent behavior across hosts and thin adapters. One source prevents prompt drift while preserving enforceable rules in code.

**Alternatives considered**:

- Separate Codex and Claude prompts: rejected because they would inevitably diverge.
- Move semantic behavior into a second model service: rejected by scope and local-first constraints.

## Decision 4: Fixture-Driven Acceptance Organized by Invariant

**Decision**: Use four readable reference fixtures and group AT coverage into consent, learning/control, cross-host, and reliability suites.

**Rationale**: The grouping avoids sixteen repetitive modules while keeping each AT explicitly parameterized and traceable. Fixtures are inspectable input and expected-state data, not a simulated domain implementation.

**Alternatives considered**:

- One large scenario runner framework: rejected as unnecessary abstraction.
- Fully mocked end-to-end tests: rejected because integration coverage must consume real promoted producer outputs.

## Decision 5: Evidence Metadata, Final Verdict Elsewhere

**Decision**: C008 records complete component-run metadata, while the integration owner creates the authoritative edge coverage manifest and final verdict.

**Rationale**: This preserves ownership and avoids dual writers to orchestration and release records.

**Alternatives considered**:

- C008 edits final implementation status: rejected because final acceptance and shared docs are integration-owned.
- Chat-only results: rejected because commands, environments, inputs, and outputs must be reproducible.

## Decision 6: Consume C004 Mastery Policy Exactly

**Decision**: Acceptance tests assert that only `pass` evidence is eligible for demonstrated-mastery advancement; `partial`, `fail`, and `insufficient_evidence` stay inspectable and contribute zero advancement. Numeric thresholds remain configurable but cannot bypass autonomous-state safeguards.

**Rationale**: This is the finalized upstream C004 contract. C008 validates it but does not implement a competing summary policy.

**Alternatives considered**: None in C008; the semantic choice is upstream-owned and final.

## Resolved Technical Context

- Runtime, dependency versions, host mechanisms, and Basic Memory compatibility are supplied by promoted C001 artifacts.
- C008 introduces no storage schema and no additional runtime dependency.
- Live-host automation uses only capabilities proven by C001/C005/C006; unsupported automation is recorded accurately rather than simulated.
- Offline validation separates expertiseOS network access from configured host-model inference.
