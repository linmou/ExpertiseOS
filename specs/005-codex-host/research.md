# Research: Codex Host Adapter

## Decision 1: Treat G0 as an Evidence Dependency

**Decision**: Do not select or name a Codex hook, plugin API, event type, or supported version in this component plan. Consume the exact released/supported mechanism only after G0 provides executable or reproducible proof for activation, actual-user capture, session identity, safe checkpoints, and failure isolation.

**Rationale**: The PRD says official documentation makes integration plausible but does not prove complete event visibility; it also warns that some Codex tool paths may bypass default hooks. Naming an unverified mechanism would turn an explicit feasibility gate into a false support claim.

**Alternatives considered**: Infer support from documentation links; use private host internals; accept model-supplied approval. All violate the MVP plan or consent boundary.

## Decision 2: Thin Event Translation

**Decision**: Keep all raw Codex payload parsing and capability discovery in `hosts/codex.py`, emitting only the promoted HostAdapter contract's normalized facts.

**Rationale**: Domain code must remain host-neutral, and Codex differences must not fork approval, retrieval, control, or learning semantics.

**Alternatives considered**: Codex-specific approval state machine; generic event bus; copied service logic. Each adds duplication without satisfying a requirement.

## Decision 3: Minimal Volatile Session State

**Decision**: Track only adapter/session identity, immutable capability snapshot, atomic depth or equivalent safe-state token, comparison-due flag, active proposal reference/binding, and last actual-user event reference.

**Rationale**: These values are sufficient to defer prompts, bind a response, and clean up at session end. Candidate payload and unused grants remain owned by upstream volatile services.

**Alternatives considered**: Durable event log, transcript cache, retry queue, scheduler. Each creates prohibited persistence or orchestration.

## Decision 4: Deterministic Decision Interpretation

**Decision**: Interpret only clear supported interaction controls for one active proposal. Ambiguous, unrelated, quoted, multiple-proposal, or edit-without-final-content inputs create no grant; the host can ask for clarification and wait for another actual-user event.

**Rationale**: Convenience cannot weaken exact approval binding, and a separate language classifier would require another model or unsafe heuristics.

**Alternatives considered**: Free-form pattern scoring; host-model assertion that the user approved; generic tool permission. None proves authorization.

## Decision 5: Capability-First Degradation

**Decision**: Derive each capability independently from the G0 matrix. Missing decision provenance makes the adapter read-only; missing atomic-boundary proof prevents proactive checkpoint behavior; missing automatic activation proof is reported rather than hidden. Runtime failures suppress expertiseOS side effects while Codex work proceeds.

**Rationale**: This gives users accurate behavior without weakening core semantics or claiming parity.

**Alternatives considered**: One global supported flag; optimistic fallback; blocking host work until service recovery. These obscure risk or violate fail-open behavior.

## Decision 6: Verification Layers

**Decision**: Use contract fixtures with verified captured/redacted payload shapes, service-failure integration fixtures, and pinned live-host fixtures. Reuse upstream fakes and avoid a large host simulator.

**Rationale**: Pure tests cover state and negative cases quickly, while only live evidence can validate event provenance and activation. Both are required and serve different claims.

**Alternatives considered**: Mock-only acceptance; transcript-only demo; live-only suite. None gives both deterministic coverage and boundary proof.
